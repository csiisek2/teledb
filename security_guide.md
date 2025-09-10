# TeleDB 보안 설정 가이드

## 봇 보안 기능 활성화 방법

TeleDB 봇은 다양한 보안 옵션을 제공합니다. `.env` 파일에서 설정할 수 있습니다.

## 보안 설정 옵션

### 1. 기본 보안 모드
```
SECURITY_ENABLED=true
```
- 기본 보안 기능 활성화

### 2. 패스워드 인증
```
ACCESS_PASSWORD=your_password_here
```
- 모든 사용자가 봇 사용 전 패스워드 입력 필요
- 사용법: `/auth 패스워드`
- 로그아웃: `/logout`

### 3. 허용된 사용자만 접근
```
ALLOWED_USERS=123456789,987654321
```
- 특정 텔레그램 사용자 ID만 봇 사용 허용
- 여러 사용자는 쉼표로 구분

### 4. 속도 제한
```
RATE_LIMIT_ENABLED=true
```
- 1분당 최대 10회 조회 제한
- 과도한 사용 방지

## 사용자 ID 확인 방법

1. 텔레그램에서 @userinfobot 찾기
2. `/start` 명령어 입력
3. 표시되는 숫자가 사용자 ID

## 보안 설정 예시

### 예시 1: 패스워드만 사용
```
# .env 파일
BOT_TOKEN=8225656341:AAHlcI8g7wGfNz2qwnDP4UUFqPllggJ-ewc
ADMIN_USER_ID=your_user_id
ACCESS_PASSWORD=mysecretpassword
RATE_LIMIT_ENABLED=true
DATABASE_PATH=./teledb.sqlite
```

### 예시 2: 특정 사용자만 허용
```
# .env 파일
BOT_TOKEN=8225656341:AAHlcI8g7wGfNz2qwnDP4UUFqPllggJ-ewc
ADMIN_USER_ID=123456789
ALLOWED_USERS=123456789,987654321,555666777
RATE_LIMIT_ENABLED=true
DATABASE_PATH=./teledb.sqlite
```

### 예시 3: 최대 보안 (패스워드 + 사용자 제한)
```
# .env 파일
BOT_TOKEN=8225656341:AAHlcI8g7wGfNz2qwnDP4UUFqPllggJ-ewc
ADMIN_USER_ID=123456789
ALLOWED_USERS=123456789,987654321
ACCESS_PASSWORD=topsecret123
SECURITY_ENABLED=true
RATE_LIMIT_ENABLED=true
DATABASE_PATH=./teledb.sqlite
```

## 보안 관리 명령어

### 사용자 명령어
- `/auth 패스워드` - 인증하기
- `/logout` - 로그아웃

### 관리자 명령어
- `/security` - 현재 보안 설정 확인

## 보안 수준별 추천 설정

### 🔓 개방형 (개발/테스트용)
```
# 보안 설정 없음
BOT_TOKEN=your_token
ADMIN_USER_ID=your_id
```

### 🔒 기본 보안
```
RATE_LIMIT_ENABLED=true
ACCESS_PASSWORD=your_password
```

### 🔐 높은 보안
```
SECURITY_ENABLED=true
ALLOWED_USERS=특정_사용자_ID들
ACCESS_PASSWORD=강력한_패스워드
RATE_LIMIT_ENABLED=true
```

## 주의사항

1. **패스워드 보안**: 추측하기 어려운 강력한 패스워드 사용
2. **사용자 ID**: 신뢰할 수 있는 사용자의 ID만 추가
3. **환경변수 보호**: `.env` 파일을 git에 커밋하지 마세요
4. **정기 확인**: `/security` 명령어로 설정 상태 정기 확인

## 문제 해결

### 봇에 접근할 수 없을 때
1. ADMIN_USER_ID가 올바른지 확인
2. 패스워드가 정확한지 확인
3. 사용자 ID가 ALLOWED_USERS에 포함되어 있는지 확인

### 속도 제한에 걸렸을 때
- 1분 후 다시 시도하세요
- 과도한 사용을 피하세요

이 설정으로 봇을 안전하게 보호할 수 있습니다!