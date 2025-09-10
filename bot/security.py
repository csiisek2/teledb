"""
텔레그램 봇 보안 기능
"""

import os
import time
import logging
from typing import Dict, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 허용된 사용자 목록 (환경변수로 관리)
ALLOWED_USERS = set()
if os.getenv('ALLOWED_USERS'):
    ALLOWED_USERS = set(map(int, os.getenv('ALLOWED_USERS').split(',')))

# 관리자 사용자
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
if ADMIN_USER_ID:
    ALLOWED_USERS.add(ADMIN_USER_ID)

# 보안 설정
SECURITY_ENABLED = os.getenv('SECURITY_ENABLED', 'false').lower() == 'true'
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD', '')
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'

# 사용자 세션 관리
authenticated_users: Set[int] = set()
user_access_times: Dict[int, datetime] = {}
user_query_counts: Dict[int, int] = {}
user_last_query_time: Dict[int, datetime] = {}

class SecurityManager:
    """보안 관리 클래스"""
    
    @staticmethod
    def is_security_enabled():
        """보안이 활성화되어 있는지 확인"""
        return SECURITY_ENABLED or ACCESS_PASSWORD or ALLOWED_USERS
    
    @staticmethod
    def is_user_allowed(user_id: int) -> bool:
        """사용자가 허용된 사용자인지 확인"""
        # 보안이 비활성화된 경우 모든 사용자 허용
        if not SecurityManager.is_security_enabled():
            return True
        
        # 허용된 사용자 목록이 있는 경우 체크
        if ALLOWED_USERS:
            return user_id in ALLOWED_USERS
        
        # 패스워드가 설정된 경우 인증된 사용자만 허용
        if ACCESS_PASSWORD:
            return user_id in authenticated_users
        
        return True
    
    @staticmethod
    def authenticate_user(user_id: int, password: str) -> bool:
        """사용자 인증"""
        if not ACCESS_PASSWORD:
            return True
        
        if password == ACCESS_PASSWORD:
            authenticated_users.add(user_id)
            user_access_times[user_id] = datetime.now()
            logger.info(f"사용자 {user_id} 인증 성공")
            return True
        
        logger.warning(f"사용자 {user_id} 인증 실패")
        return False
    
    @staticmethod
    def logout_user(user_id: int):
        """사용자 로그아웃"""
        authenticated_users.discard(user_id)
        user_access_times.pop(user_id, None)
        logger.info(f"사용자 {user_id} 로그아웃")
    
    @staticmethod
    def is_rate_limited(user_id: int) -> bool:
        """사용자가 속도 제한에 걸렸는지 확인"""
        if not RATE_LIMIT_ENABLED:
            return False
        
        now = datetime.now()
        
        # 1분 내 최대 10회 조회 제한
        last_query = user_last_query_time.get(user_id)
        if last_query:
            if now - last_query < timedelta(minutes=1):
                count = user_query_counts.get(user_id, 0)
                if count >= 10:
                    return True
            else:
                # 1분이 지났으면 카운트 리셋
                user_query_counts[user_id] = 0
        
        return False
    
    @staticmethod
    def record_query(user_id: int):
        """사용자 조회 기록"""
        now = datetime.now()
        user_last_query_time[user_id] = now
        user_query_counts[user_id] = user_query_counts.get(user_id, 0) + 1
    
    @staticmethod
    def cleanup_old_sessions():
        """오래된 세션 정리 (24시간 후 만료)"""
        now = datetime.now()
        expired_users = []
        
        for user_id, access_time in user_access_times.items():
            if now - access_time > timedelta(hours=24):
                expired_users.append(user_id)
        
        for user_id in expired_users:
            SecurityManager.logout_user(user_id)
    
    @staticmethod
    def get_security_info() -> str:
        """보안 설정 정보 반환"""
        info = []
        
        if SECURITY_ENABLED:
            info.append("🔒 보안 모드 활성화")
        
        if ACCESS_PASSWORD:
            info.append("🔐 패스워드 인증 필요")
        
        if ALLOWED_USERS:
            info.append(f"👥 허용된 사용자: {len(ALLOWED_USERS)}명")
        
        if RATE_LIMIT_ENABLED:
            info.append("⏱️ 속도 제한: 1분당 10회")
        
        if len(authenticated_users) > 0:
            info.append(f"✅ 인증된 사용자: {len(authenticated_users)}명")
        
        return '\n'.join(info) if info else "🔓 보안 비활성화"

def check_user_access(user_id: int, username: str = None) -> tuple[bool, str]:
    """사용자 접근 권한 확인 (동적 승인 시스템)"""
    
    # dis7414는 항상 접근 가능 (슈퍼어드민)
    if username == "dis7414":
        return True, ""
    
    # 속도 제한 확인
    if SecurityManager.is_rate_limited(user_id):
        return False, "⏱️ 너무 많은 요청입니다. 1분 후 다시 시도해주세요."
    
    # 동적 승인 시스템 사용
    from bot.handlers import approved_users
    
    # username 또는 user_id가 승인되었는지 확인
    if username and username in approved_users:
        return True, ""
    
    if user_id in approved_users:
        return True, ""
    
    # 기존 보안 시스템도 체크
    if SecurityManager.is_user_allowed(user_id):
        if ACCESS_PASSWORD:
            return False, "🔐 봇 사용을 위해 먼저 인증해주세요.\n`/auth 패스워드`를 입력하세요."
        return True, ""
    
    # 승인되지 않은 사용자
    return False, "🚫 이 봇을 사용하려면 관리자의 승인이 필요합니다.\n관리자에게 문의해주세요."

# 주기적으로 오래된 세션 정리
import threading
def cleanup_sessions():
    while True:
        time.sleep(3600)  # 1시간마다
        SecurityManager.cleanup_old_sessions()

cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
cleanup_thread.start()