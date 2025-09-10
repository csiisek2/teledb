#!/usr/bin/env python3
"""
Render Web Service용 텔레그램 봇 통합 서버
웹훅 + Flask 통합 처리
"""

import os
import asyncio
import logging
from flask import Flask, request
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

# Flask 웹 서버
app = Flask(__name__)

# 전역 변수
application = None
bot_token = None

@app.route('/')
def health_check():
    return "TeleDB 봇이 실행 중입니다! 🤖", 200

@app.route('/health')
def health():
    return {"status": "ok", "service": "teledb-bot"}, 200

@app.route(f'/<webhook_token>', methods=['POST'])
def webhook(webhook_token):
    """텔레그램 웹훅 처리"""
    global application, bot_token
    
    if webhook_token != bot_token:
        logger.warning(f"잘못된 웹훅 토큰: {webhook_token}")
        return "Forbidden", 403
    
    if application:
        # 비동기 업데이트 처리 (Flask-safe)
        update_data = request.get_json()
        if update_data:
            # 새 이벤트 루프에서 처리
            import threading
            threading.Thread(target=run_update_sync, args=(update_data,), daemon=True).start()
    
    return "OK", 200

def run_update_sync(update_data):
    """동기 환경에서 비동기 업데이트 처리"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 업데이트 처리 전에 약간 대기
        loop.run_until_complete(asyncio.sleep(0.1))
        loop.run_until_complete(process_update(update_data))
        
        # 모든 태스크가 완료될 때까지 대기
        pending = asyncio.all_tasks(loop)
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        # 짧은 대기 후 루프 종료
        loop.run_until_complete(asyncio.sleep(0.5))
        
    except Exception as e:
        logger.error(f"업데이트 처리 중 오류: {e}")
    finally:
        try:
            if loop and not loop.is_closed():
                loop.close()
        except:
            pass

async def process_update(update_data):
    """업데이트 비동기 처리"""
    from telegram import Update
    try:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"업데이트 처리 중 오류: {e}")

async def setup_bot():
    """봇 설정 및 웹훅 등록"""
    global application, bot_token
    
    # 환경변수 확인
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN이 설정되지 않았습니다.")
        return False
    
    # 데이터베이스 초기화
    try:
        init_database()
        logger.info("데이터베이스 초기화 성공")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
    
    # 텔레그램 애플리케이션 생성
    application = Application.builder().token(bot_token).build()
    await application.initialize()
    
    # 웹훅 설정
    webhook_url = f"https://teledb-1.onrender.com/{bot_token}"
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=webhook_url)
    
    # 핸들러 설정  
    setup_handlers(application)
    
    logger.info(f"웹훅 설정 완료: {webhook_url}")
    return True

if __name__ == '__main__':
    # 비동기 봇 설정
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(setup_bot())
    
    if success:
        logger.info("봇 설정 완료 - Flask 서버 시작")
        port = int(os.environ.get('PORT', 10000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.error("봇 설정 실패")