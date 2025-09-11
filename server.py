#!/usr/bin/env python3
"""
간단한 폴링 방식 텔레그램 봇 + Flask 서버
"""

import os
import asyncio
import logging
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram.ext import Application
from bot.handlers import setup_handlers
from bot.database_postgres import init_database

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask 웹 서버 (포트 바인딩용)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "TeleDB 봇이 실행 중입니다! 🤖", 200

@app.route('/health')
def health():
    return {"status": "ok", "service": "teledb-bot"}, 200

async def run_bot():
    """텔레그램 봇 실행"""
    # 환경변수 확인
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
    
    # 텔레그램 애플리케이션 생성
    application = Application.builder().token(bot_token).build()
    await application.initialize()
    
    # 웹훅 삭제하고 폴링 방식으로 실행
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("웹훅 삭제 완료 - 폴링 모드로 시작")
    
    # 다른 인스턴스가 종료될 시간을 기다림
    import asyncio
    logger.info("다른 봇 인스턴스 종료 대기 중... (30초)")
    await asyncio.sleep(30)
    
    # 핸들러 설정
    setup_handlers(application)
    
    # 봇 시작 (재시도 로직 포함)
    await application.start()
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            await application.updater.start_polling()
            logger.info("폴링 시작 성공!")
            break
        except Exception as e:
            logger.error(f"폴링 시작 실패 (시도 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                wait_time = 10 * (attempt + 1)
                logger.info(f"{wait_time}초 후 재시도...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("폴링 시작 최종 실패")
                raise
    
    logger.info("텔레그램 봇 폴링 시작 완료")
    
    try:
        # 무한 대기
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("봇이 종료됩니다...")
    finally:
        await application.stop()
        await application.shutdown()

def start_bot():
    """별도 스레드에서 봇 실행"""
    try:
        asyncio.run(run_bot())
    except Exception as e:
        logger.error(f"봇 실행 중 오류: {e}")

if __name__ == '__main__':
    # 봇을 별도 스레드에서 실행
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    logger.info("Flask 서버 시작")
    
    # Flask 웹서버 실행 (포트 바인딩용)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)