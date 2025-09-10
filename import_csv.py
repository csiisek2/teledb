#!/usr/bin/env python3
"""
CSV 파일을 단순화된 TeleDB SQLite 데이터베이스로 가져오는 스크립트
새 구조: phone_number + content (중복 허용)
"""

import csv
import os
import sys
from dotenv import load_dotenv

# 현재 디렉토리를 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import init_database, add_phone_data
from bot.utils import clean_phone_number, validate_phone_number

def import_csv_to_database(csv_file_path, encoding='utf-8'):
    """CSV 파일을 단순화된 데이터베이스로 가져오기"""
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV 파일을 찾을 수 없습니다: {csv_file_path}")
        return
    
    # 환경변수 로드 및 데이터베이스 초기화
    load_dotenv()
    init_database()
    
    print(f"📁 CSV 파일 가져오기: {csv_file_path}")
    
    success_count = 0
    error_count = 0
    skip_count = 0
    
    try:
        with open(csv_file_path, 'r', encoding=encoding, newline='') as csvfile:
            # CSV 파일의 첫 번째 줄을 읽어서 구분자 감지
            sample = csvfile.read(1024)
            csvfile.seek(0)
            
            # 구분자 자동 감지
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            print(f"📋 감지된 구분자: '{delimiter}'")
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # 헤더 정보 출력
            headers = reader.fieldnames
            print(f"📊 헤더 정보: {headers}")
            
            # 헤더 매핑 (한글/영어 모두 지원)
            field_mapping = detect_field_mapping(headers)
            print(f"🔗 필드 매핑: {field_mapping}")
            
            if not field_mapping.get('phone_number'):
                print("❌ 전화번호 필드를 찾을 수 없습니다.")
                print("   지원하는 헤더명: phone, phone_number, 전화번호, 휴대폰, 연락처")
                return
            
            # 데이터 가져오기
            for row_num, row in enumerate(reader, 1):
                try:
                    # 전화번호 추출 및 정리
                    phone_raw = row.get(field_mapping['phone_number'], '').strip()
                    if not phone_raw:
                        skip_count += 1
                        continue
                    
                    phone_number = clean_phone_number(phone_raw)
                    
                    # 전화번호 유효성 검사
                    if not validate_phone_number(phone_number):
                        print(f"   ⚠️ 줄 {row_num}: 잘못된 전화번호 형식 '{phone_raw}' 건너뛰기")
                        skip_count += 1
                        continue
                    
                    # 모든 필드를 하나의 content로 합치기
                    content_parts = []
                    
                    # 순서대로 필드 처리
                    for field_name in ['name', 'company', 'address', 'email', 'notes']:
                        if field_mapping.get(field_name):
                            value = row.get(field_mapping[field_name], '').strip()
                            if value:
                                field_korean = {
                                    'name': '이름',
                                    'company': '회사', 
                                    'address': '주소',
                                    'email': '이메일',
                                    'notes': '메모'
                                }[field_name]
                                content_parts.append(f"{field_korean}: {value}")
                    
                    # 만약 매핑되지 않은 필드들이 있다면 추가
                    for header in headers:
                        if header not in field_mapping.values():
                            value = row.get(header, '').strip()
                            if value and header != field_mapping.get('phone_number'):
                                content_parts.append(f"{header}: {value}")
                    
                    content = " | ".join(content_parts) if content_parts else "정보 없음"
                    
                    # 데이터베이스에 추가 (중복 허용)
                    result = add_phone_data(phone_number, content)
                    
                    if result:
                        success_count += 1
                        if success_count % 100 == 0:
                            print(f"   📊 진행률: {success_count}개 완료...")
                    else:
                        print(f"   ❌ 줄 {row_num}: {phone_number} 추가 실패")
                        error_count += 1
                        
                except Exception as e:
                    print(f"   ❌ 줄 {row_num}: 오류 발생 - {e}")
                    error_count += 1
                    
    except UnicodeDecodeError:
        print(f"❌ 인코딩 오류. 다른 인코딩을 시도해보세요:")
        print(f"   python3 import_csv.py {csv_file_path} cp949")
        return
    except Exception as e:
        print(f"❌ CSV 파일 읽기 오류: {e}")
        return
    
    # 결과 요약
    print(f"\n📈 가져오기 완료!")
    print(f"   ✅ 성공: {success_count}개")
    print(f"   ⚠️ 건너뛴 항목: {skip_count}개")
    print(f"   ❌ 오류: {error_count}개")
    print(f"   📊 총 처리: {success_count + skip_count + error_count}개")

def detect_field_mapping(headers):
    """헤더에서 필드 매핑 자동 감지"""
    mapping = {}
    
    # 가능한 헤더명들 (소문자로 변환해서 비교)
    field_patterns = {
        'phone_number': ['phone', 'phone_number', 'phonenumber', 'mobile', 'tel', 
                        '전화번호', '휴대폰', '연락처', '핸드폰', '휴대전화'],
        'name': ['name', 'full_name', 'fullname', 'user_name', 'username',
                '이름', '성명', '고객명', '사용자명'],
        'company': ['company', 'corp', 'corporation', 'organization', 'org',
                   '회사', '회사명', '직장', '기업', '업체'],
        'address': ['address', 'addr', 'location', 'place',
                   '주소', '거주지', '위치', '소재지'],
        'email': ['email', 'e_mail', 'mail', 'email_address',
                 '이메일', '메일', '전자우편'],
        'notes': ['notes', 'note', 'memo', 'comment', 'description', 'desc',
                 '메모', '비고', '설명', '참고', '노트']
    }
    
    # 각 헤더에 대해 매칭 시도
    for header in headers:
        header_lower = header.lower().strip()
        
        for field, patterns in field_patterns.items():
            if header_lower in [p.lower() for p in patterns]:
                mapping[field] = header
                break
    
    return mapping

def create_sample_csv():
    """단순화된 샘플 CSV 파일 생성"""
    sample_csv_path = './sample_contacts_simple.csv'
    
    sample_data = [
        ['전화번호', '이름', '회사', '주소', '메모'],
        ['010-1234-5678', '김철수', 'ABC회사', '서울시 강남구', '중요고객'],
        ['010-1234-5678', '김철수 (대리)', 'ABC회사 영업팀', '서울시 강남구', '같은 번호 다른 정보'],
        ['010-9876-5432', '이영희', 'XYZ기업', '부산시 해운대구', ''],
        ['011-111-2222', '박민호', '대한상사', '대구시 수성구', 'VIP'],
        ['010-5555-6666', '정수진', '글로벌텍', '인천시 연수구', '신규고객'],
    ]
    
    with open(sample_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(sample_data)
    
    print(f"📝 단순화된 샘플 CSV 파일이 생성되었습니다: {sample_csv_path}")
    print("💡 같은 전화번호에 다른 정보가 포함된 예시입니다.")
    return sample_csv_path

def show_help():
    """도움말 출력"""
    print("""
📁 단순화된 CSV 가져오기 도구 (중복 허용)

사용법:
  python3 import_csv.py <CSV파일경로> [인코딩]

예시:
  python3 import_csv.py contacts.csv
  python3 import_csv.py contacts.csv utf-8
  python3 import_csv.py contacts.csv cp949

새로운 특징:
  🔄 중복 허용: 같은 전화번호에 여러 정보 추가 가능
  📝 단순 구조: phone_number + content 형태로 저장
  🔍 통합 조회: 한 번호의 모든 정보를 한 번에 표시

인코딩 옵션:
  utf-8    - 기본값 (UTF-8)
  cp949    - 한국어 Windows (EUC-KR)
  euc-kr   - 한국어 리눅스

지원하는 CSV 헤더:
  전화번호: phone, phone_number, 전화번호, 휴대폰, 연락처
  이름:     name, full_name, 이름, 성명, 고객명
  회사:     company, corp, 회사, 회사명, 직장
  주소:     address, addr, 주소, 거주지, 위치
  이메일:   email, e_mail, 이메일, 메일
  메모:     notes, memo, 메모, 비고, 설명

명령어:
  sample   - 단순화된 샘플 CSV 파일 생성
  help     - 이 도움말 출력
""")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == 'help':
        show_help()
    elif sys.argv[1] == 'sample':
        sample_path = create_sample_csv()
        print(f"\n샘플 CSV를 가져오려면:")
        print(f"python3 import_csv.py {sample_path}")
    else:
        csv_file = sys.argv[1]
        encoding = sys.argv[2] if len(sys.argv) > 2 else 'utf-8'
        import_csv_to_database(csv_file, encoding)