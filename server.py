#!/usr/bin/env python3
"""
Render Web Service용 텔레그램 봇 래퍼
포트 바인딩 + 봇 실행
"""

import os
import asyncio
import threading
from flask import Flask
from main import main as bot_main

# Flask 웹 서버 (포트 바인딩용)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "TeleDB 봇이 실행 중입니다! 🤖", 200

@app.route('/health')
def health():
    return {"status": "ok", "service": "teledb-bot"}, 200

def run_bot():
    """백그라운드에서 봇 실행"""
    try:
        asyncio.run(bot_main())
    except Exception as e:
        print(f"봇 실행 중 오류: {e}")

if __name__ == '__main__':
    # 봇을 별도 스레드에서 실행
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Flask 웹서버 실행 (포트 바인딩용)
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)