"""
설정 관리
"""

import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 봇 설정
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

# 데이터베이스 설정
DATABASE_PATH = os.getenv('DATABASE_PATH', './teledb.sqlite')
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL용 (미래 확장)

# 기타 설정
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

def validate_config():
    """설정 값 검증"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN이 설정되지 않았습니다.")
    
    if ADMIN_USER_ID == 0:
        errors.append("ADMIN_USER_ID가 설정되지 않았습니다.")
    
    return errors