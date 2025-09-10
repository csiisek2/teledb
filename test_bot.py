#!/usr/bin/env python3
"""
단순화된 TeleDB 봇 테스트 스크립트
새 구조: phone_number + content (중복 허용)
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv

# 현재 디렉토리를 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import init_database, search_phone, add_phone_data, get_stats
from bot.utils import validate_phone_number, format_phone_number, clean_phone_number

def test_database_functions():
    """단순화된 데이터베이스 함수들 테스트"""
    print("🧪 단순화된 데이터베이스 함수 테스트 시작...")
    
    # 환경변수 로드
    load_dotenv()
    
    # 테스트용 데이터베이스 초기화
    os.environ['DATABASE_PATH'] = './test_teledb_simple.sqlite'
    init_database()
    
    # 1. 데이터 추가 테스트 (중복 허용)
    print("\n1. 데이터 추가 테스트 (중복 허용)")
    test_data = [
        ('01012345678', '이름: 홍길동 | 회사: 테스트회사 | 주소: 서울시'),
        ('01012345678', '이름: 홍길동 (대리) | 회사: 테스트회사 영업팀'),  # 같은 번호 다른 정보
        ('01098765432', '이름: 김철수 | 회사: ABC기업 | 메모: VIP고객')
    ]
    
    for phone, content in test_data:
        result = add_phone_data(phone, content)
        print(f"   추가 결과: {phone} -> {'성공' if result else '실패'}")
    
    # 2. 중복 전화번호 조회 테스트 (모든 정보 표시)
    print("\n2. 중복 전화번호 조회 테스트")
    results = search_phone('01012345678')
    if results:
        formatted_phone = format_phone_number('01012345678')
        print(f"   📱 {formatted_phone}에서 {len(results)}개 정보 발견:")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['content']}")
            print(f"      📅 등록일: {result['created_at'][:19]}")
    else:
        print("   조회 실패")
    
    # 3. 존재하지 않는 번호 조회 테스트
    print("\n3. 존재하지 않는 번호 조회 테스트")
    results = search_phone('01099999999')
    print(f"   조회 결과: {len(results)}개 (예상: 0개)")
    
    # 4. 통계 테스트
    print("\n4. 통계 테스트")
    stats = get_stats()
    print(f"   총 데이터: {stats['total_records']}개")
    print(f"   유니크 전화번호: {stats['unique_phones']}개")
    print(f"   평균: {stats['total_records'] / max(stats['unique_phones'], 1):.1f}개/번호")
    
    # 5. 전화번호 검증 테스트
    print("\n5. 전화번호 검증 테스트")
    test_numbers = [
        ('01012345678', True),
        ('010-1234-5678', False),
        ('0101234567', False),
        ('0201234567', False),
        ('01112345678', True),
    ]
    
    for number, expected in test_numbers:
        cleaned = clean_phone_number(number)
        result = validate_phone_number(cleaned)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {number} -> {cleaned}: {result} (예상: {expected})")
    
    # 테스트 데이터베이스 정리
    if os.path.exists('./test_teledb_simple.sqlite'):
        os.remove('./test_teledb_simple.sqlite')
    
    print("\n✅ 모든 테스트 완료!")

def create_sample_database():
    """단순화된 샘플 데이터베이스 생성 (중복 허용)"""
    print("📦 단순화된 샘플 데이터베이스 생성 중...")
    
    # 환경변수 로드
    load_dotenv()
    
    # 실제 데이터베이스 초기화
    init_database()
    
    # 샘플 데이터 추가 (중복 허용)
    sample_data = [
        ('01012345678', '이름: 홍길동 | 회사: 삼성전자 | 주소: 서울시 강남구 | 메모: 개발팀 팀장'),
        ('01012345678', '이름: 홍길동 (대리) | 회사: 삼성전자 기획팀 | 메모: 부서 다름'),
        ('01098765432', '이름: 김영희 | 회사: 네이버 | 주소: 경기도 분당구 | 메모: 기획팀'),
        ('01011112222', '이름: 박민수 | 회사: LG전자 | 주소: 서울시 영등포구 | 메모: 마케팅팀'),
        ('01011112222', '이름: 박민수 (본부) | 회사: LG전자 마케팅본부 | 메모: 승진함'),
        ('01033334444', '이름: 이수정 | 회사: 카카오 | 주소: 제주시 | 메모: UX 디자이너'),
        ('01055556666', '이름: 최도현 | 회사: 토스 | 주소: 서울시 강남구 | 메모: 백엔드 개발자'),
    ]
    
    for phone, content in sample_data:
        result = add_phone_data(phone, content)
        if result:
            print(f"   ✅ {format_phone_number(phone)} 추가 완료")
            print(f"      📝 {content[:50]}{'...' if len(content) > 50 else ''}")
        else:
            print(f"   ❌ {phone} 추가 실패")
    
    # 통계 출력
    stats = get_stats()
    print(f"\n📊 현재 통계:")
    print(f"   총 등록된 데이터: {stats['total_records']}개")
    print(f"   유니크 전화번호: {stats['unique_phones']}개")
    print(f"   평균: {stats['total_records'] / max(stats['unique_phones'], 1):.1f}개/번호")
    
    print("\n✅ 단순화된 샘플 데이터베이스 생성 완료!")
    print("💡 중복 번호들이 포함되어 있습니다. 텔레그램 봇에서 조회해보세요!")

def show_duplicate_examples():
    """중복 번호 조회 예시"""
    print("🔍 중복 번호 조회 예시...")
    
    load_dotenv()
    
    # 중복이 있는 번호들 조회
    duplicate_phones = ['01012345678', '01011112222']
    
    for phone in duplicate_phones:
        results = search_phone(phone)
        if len(results) > 1:
            formatted_phone = format_phone_number(phone)
            print(f"\n📱 **{formatted_phone}** ({len(results)}개 정보):")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['content']}")
                print(f"      📅 {result['created_at'][:19]}")

def show_help():
    """도움말 출력"""
    print("""
🤖 단순화된 TeleDB 테스트 스크립트 (중복 허용)

사용법:
  python3 test_bot.py [명령어]

명령어:
  test      - 데이터베이스 함수들 테스트 실행
  sample    - 샘플 데이터베이스 생성 (중복 포함)
  duplicate - 중복 번호 조회 예시
  help      - 이 도움말 출력

새로운 특징:
  🔄 중복 허용: 같은 전화번호에 여러 정보
  📝 단순 구조: phone_number + content
  🔍 통합 조회: 한 번호의 모든 정보 표시

예시:
  python3 test_bot.py test
  python3 test_bot.py sample
  python3 test_bot.py duplicate
""")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == 'test':
        test_database_functions()
    elif sys.argv[1] == 'sample':
        create_sample_database()
    elif sys.argv[1] == 'duplicate':
        show_duplicate_examples()
    elif sys.argv[1] == 'help':
        show_help()
    else:
        print(f"❌ 알 수 없는 명령어: {sys.argv[1]}")
        print("사용 가능한 명령어: test, sample, duplicate, help")