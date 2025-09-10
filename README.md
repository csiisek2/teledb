# TeleDB - 텔레그램 봇 전화번호 조회 시스템

전화번호를 입력하면 해당 정보를 데이터베이스에서 조회하여 반환하는 텔레그램 봇입니다.

## 🚀 빠른 시작

### 1. 텔레그램 봇 생성
1. [@BotFather](https://t.me/BotFather)에게 `/newbot` 명령 전송
2. 봇 이름과 사용자명 설정
3. 발급받은 토큰을 메모

### 2. 관리자 사용자 ID 확인
1. [@userinfobot](https://t.me/userinfobot)에게 `/start` 명령 전송
2. 반환된 사용자 ID를 메모

### 3. 로컬 개발 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd teledb

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어서 BOT_TOKEN과 ADMIN_USER_ID 설정

# 봇 실행
python main.py
```

### 4. Railway 배포 (무료)

1. [Railway](https://railway.app)에 GitHub 계정으로 회원가입
2. "Deploy from GitHub repo" 클릭
3. 환경변수 설정:
   - `BOT_TOKEN`: 텔레그램 봇 토큰
   - `ADMIN_USER_ID`: 관리자 사용자 ID
4. 자동 배포 완료!

## 📱 사용법

### 일반 사용자 명령어
- `/start` - 시작 및 환영 메시지
- `/search 01012345678` - 전화번호 조회
- `/help` - 도움말
- `/stats` - 통계 보기
- 전화번호 직접 입력 (예: `01012345678`)

### 관리자 전용 명령어
- `/add 01012345678:홍길동:삼성전자:서울시 강남구` - 새 정보 추가
- `/update 01012345678:name:김철수` - 정보 수정
- `/delete 01012345678` - 정보 삭제

## 🏗️ 프로젝트 구조

```
teledb/
├── bot/
│   ├── __init__.py
│   ├── handlers.py      # 텔레그램 명령어 핸들러
│   ├── database.py      # SQLite 데이터베이스 연결
│   └── utils.py         # 유틸리티 함수들
├── config/
│   ├── __init__.py
│   └── settings.py      # 설정 관리
├── data/               # 데이터베이스 파일 저장 디렉토리
├── main.py            # 봇 시작점
├── requirements.txt   # Python 의존성
├── .env.example       # 환경변수 예시
└── README.md
```

## 🔧 주요 기능

### ✅ 구현 완료
- [x] SQLite 기반 데이터베이스
- [x] 전화번호 조회 기능
- [x] 관리자 권한 시스템
- [x] CRUD 작업 (추가/조회/수정/삭제)
- [x] 조회 로그 및 통계
- [x] 자동 전화번호 형식 검증
- [x] Railway 배포 지원

### 🚧 향후 계획
- [ ] PostgreSQL 마이그레이션 도구
- [ ] 대량 데이터 가져오기/내보내기
- [ ] Redis 캐싱 레이어
- [ ] 웹 관리 대시보드

## 🔒 보안 기능

- 관리자 권한 검증
- SQL 인젝션 방지
- 입력값 검증 및 필터링
- 조회 기록 추적

## 📊 데이터베이스 스키마

### phone_data 테이블
- `id`: 자동 증가 ID
- `phone_number`: 전화번호 (고유)
- `name`: 이름
- `company`: 회사명
- `address`: 주소
- `email`: 이메일
- `notes`: 메모
- `created_at`: 생성일시
- `updated_at`: 수정일시

### query_logs 테이블
- `id`: 자동 증가 ID
- `user_id`: 조회한 사용자 ID
- `username`: 사용자명
- `query_phone`: 조회한 전화번호
- `found`: 조회 성공 여부
- `query_time`: 조회 시각

## 📁 CSV 데이터 가져오기

기존 CSV 파일의 연락처 데이터를 데이터베이스로 가져올 수 있습니다.

### 사용법
```bash
# CSV 파일 가져오기 (UTF-8)
python3 import_csv.py contacts.csv

# 한글 Windows CSV (CP949/EUC-KR)
python3 import_csv.py contacts.csv cp949

# 샘플 CSV 파일 생성
python3 import_csv.py sample
```

### 지원하는 CSV 헤더
| 필드 | 지원하는 헤더명 |
|------|----------------|
| 전화번호 | phone, phone_number, 전화번호, 휴대폰, 연락처 |
| 이름 | name, full_name, 이름, 성명, 고객명 |
| 회사 | company, corp, 회사, 회사명, 직장 |
| 주소 | address, addr, 주소, 거주지, 위치 |
| 이메일 | email, e_mail, 이메일, 메일 |
| 메모 | notes, memo, 메모, 비고, 설명 |

### CSV 파일 예시
```csv
전화번호,이름,회사,주소,이메일,메모
010-1234-5678,김철수,ABC회사,서울시 강남구,kim@abc.com,중요고객
010-9876-5432,이영희,XYZ기업,부산시 해운대구,lee@xyz.co.kr,
```

## 🛠️ 개발 도구

### 로컬 테스팅
```bash
# 데이터베이스 내용 확인
sqlite3 teledb.sqlite "SELECT * FROM phone_data;"

# 조회 로그 확인
sqlite3 teledb.sqlite "SELECT * FROM query_logs ORDER BY query_time DESC LIMIT 10;"
```

### 디버깅
- 환경변수 `DEBUG=true` 설정시 상세 로그 출력
- `LOG_LEVEL` 환경변수로 로그 레벨 조정

## 🤝 기여하기

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이센스

This project is licensed under the MIT License.

## 📞 지원

문제가 있거나 기능 요청이 있으시면 GitHub Issues를 통해 알려주세요.