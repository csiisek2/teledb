#!/usr/bin/env python3
"""
TeleDB - 텔레그램 봇 전화번호 조회 시스템
메인 엔트리 포인트
"""

import logging
import os
from dotenv import load_dotenv
from telegram.ext import Application

from bot.handlers import setup_handlers
from bot.database_postgres import init_database

# 환경변수 로드
load_dotenv()

# 로깅 설정 (DEBUG 모드)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

async def main():
    """메인 함수"""
    
    # 환경변수 디버그 정보
    logger.info("=== 환경변수 디버그 정보 ===")
    logger.info(f"BOT_TOKEN 존재: {bool(os.getenv('BOT_TOKEN'))}")
    logger.info(f"DATABASE_URL 존재: {bool(os.getenv('DATABASE_URL'))}")
    if os.getenv('DATABASE_URL'):
        db_url = os.getenv('DATABASE_URL')
        # 보안을 위해 앞 20자, 뒤 10자만 표시
        masked_url = db_url[:20] + "***" + db_url[-10:] if len(db_url) > 30 else db_url
        logger.info(f"DATABASE_URL 형태: {masked_url}")
    logger.info("========================")
    
    # 봇 토큰 확인
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN이 설정되지 않았습니다.")
        return
    
    # 데이터베이스 초기화
    try:
        init_database()
        logger.info("데이터베이스 초기화 성공")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        # 계속 진행 - 폴백으로 작동
    
    # 텔레그램 애플리케이션 생성
    application = Application.builder().token(bot_token).build()
    
    # 애플리케이션 초기화 (Python 3.13 호환성)
    await application.initialize()
    
    # 핸들러 설정
    setup_handlers(application)
    
    logger.info("텔레그램 봇이 시작됩니다...")
    
    try:
        # 봇 실행
        await application.start()
        await application.updater.start_polling()
        
        # 종료 신호까지 대기
        import asyncio
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("봇이 종료됩니다...")
    finally:
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())