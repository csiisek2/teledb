"""
PostgreSQL 데이터베이스 연결 및 쿼리 처리
구조: phone_number + content (중복 허용)
"""

import psycopg
import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict
import urllib.parse as urlparse

logger = logging.getLogger(__name__)

# PostgreSQL 연결 정보
DATABASE_URL = os.getenv('DATABASE_URL', '')
USE_SQLITE_FALLBACK = True  # 임시 SQLite 폴백 활성화

def get_connection():
    """PostgreSQL 연결 반환 (SQLite 폴백 포함)"""
    logger.info(f"=== 데이터베이스 연결 디버그 ===")
    logger.info(f"DATABASE_URL 길이: {len(DATABASE_URL) if DATABASE_URL else 0}")
    logger.info(f"DATABASE_URL 시작: {DATABASE_URL[:30] if DATABASE_URL else 'None'}")
    logger.info(f"USE_SQLITE_FALLBACK: {USE_SQLITE_FALLBACK}")
    
    try:
        if not DATABASE_URL:
            logger.warning("DATABASE_URL 환경변수가 설정되지 않음 - SQLite 사용")
            if USE_SQLITE_FALLBACK:
                return get_sqlite_connection()
            raise ValueError("DATABASE_URL이 없습니다")
        
        logger.info(f"PostgreSQL 연결 시도: {DATABASE_URL[:50]}...")
        
        # 연결 전 URL 유효성 검사
        if not DATABASE_URL.startswith(('postgresql://', 'postgres://')):
            logger.error(f"잘못된 DATABASE_URL 형태: {DATABASE_URL[:30]}")
            raise ValueError("DATABASE_URL이 올바른 PostgreSQL URL 형태가 아닙니다")
        
        # psycopg3는 URL 직접 사용 가능
        conn = psycopg.connect(DATABASE_URL)
        logger.info("PostgreSQL 연결 성공")
        
        # 연결 테스트
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info(f"PostgreSQL 테스트 쿼리 결과: {result}")
        
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL 연결 오류: {type(e).__name__}: {e}")
        if USE_SQLITE_FALLBACK:
            logger.warning("PostgreSQL 실패 - SQLite 폴백 사용")
            return get_sqlite_connection()
        raise

def get_sqlite_connection():
    """SQLite 폴백 연결"""
    try:
        conn = sqlite3.connect('./teledb.sqlite')
        conn.row_factory = sqlite3.Row  # dict-like access
        logger.info("SQLite 폴백 연결 성공")
        return conn
    except Exception as e:
        logger.error(f"SQLite 연결도 실패: {e}")
        raise

def init_database():
    """데이터베이스 테이블 초기화"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 단순한 전화번호 정보 테이블 (중복 허용)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS phone_data (
                        id SERIAL PRIMARY KEY,
                        phone_number VARCHAR(15) NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 조회 로그 테이블 (단순화)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS query_logs (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        username VARCHAR(100),
                        query_phone VARCHAR(15),
                        results_count INTEGER DEFAULT 0,
                        query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성 (중복 허용)
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON phone_data(phone_number)')
                
                conn.commit()
                logger.info("PostgreSQL 데이터베이스 테이블이 초기화되었습니다.")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 오류: {e}")
        raise

def search_phone(phone_number: str) -> List[Dict]:
    """전화번호로 모든 매칭 정보 조회 (중복 허용)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # PostgreSQL과 SQLite 호환 쿼리
                if 'sqlite' in str(type(conn)).lower():
                    cursor.execute('''
                        SELECT * FROM phone_data 
                        WHERE phone_number = ?
                        ORDER BY created_at DESC
                    ''', (phone_number,))
                else:
                    cursor.execute('''
                        SELECT * FROM phone_data 
                        WHERE phone_number = %s
                        ORDER BY created_at DESC
                    ''', (phone_number,))
                
                results = cursor.fetchall()
                if results:
                    # PostgreSQL 결과를 dict로 변환
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                else:
                    return []
    except Exception as e:
        logger.error(f"전화번호 조회 중 오류: {e}")
        # 긴급 테스트용 더미 데이터
        logger.warning("데이터베이스 조회 실패 - 테스트 데이터 반환")
        return [{'phone_number': phone_number, 'content': '테스트 데이터 - DB 연결 확인 필요', 'created_at': '2025-01-01'}]

def add_phone_data(phone_number: str, content: str) -> bool:
    """새 전화번호 정보 추가 (중복 허용)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO phone_data (phone_number, content)
                    VALUES (%s, %s)
                ''', (phone_number, content.strip()))
                
                conn.commit()
                logger.info(f"전화번호 {phone_number} 정보가 추가되었습니다.")
                return True
    except Exception as e:
        logger.error(f"데이터 추가 중 오류: {e}")
        return False

def update_phone_data(phone_number: str, old_content: str, new_content: str) -> bool:
    """특정 전화번호의 특정 내용 수정"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    UPDATE phone_data 
                    SET content = %s
                    WHERE phone_number = %s AND content = %s
                ''', (new_content.strip(), phone_number, old_content))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"전화번호 {phone_number} 정보가 수정되었습니다.")
                    return True
                else:
                    logger.warning(f"수정할 데이터를 찾을 수 없습니다: {phone_number}")
                    return False
    except Exception as e:
        logger.error(f"데이터 수정 중 오류: {e}")
        return False

def delete_phone_data(phone_number: str, content: str = None) -> bool:
    """전화번호 정보 삭제"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                if content:
                    # 특정 내용만 삭제
                    cursor.execute('DELETE FROM phone_data WHERE phone_number = %s AND content = %s', 
                                  (phone_number, content))
                else:
                    # 해당 번호의 모든 내용 삭제
                    cursor.execute('DELETE FROM phone_data WHERE phone_number = %s', (phone_number,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    deleted_count = cursor.rowcount
                    logger.info(f"전화번호 {phone_number} 정보 {deleted_count}개가 삭제되었습니다.")
                    return True
                else:
                    logger.warning(f"삭제할 데이터를 찾을 수 없습니다: {phone_number}")
                    return False
    except Exception as e:
        logger.error(f"데이터 삭제 중 오류: {e}")
        return False

def log_query(user_id: int, username: str, query_phone: str, results_count: int):
    """조회 기록 저장"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO query_logs (user_id, username, query_phone, results_count)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, username, query_phone, results_count))
                conn.commit()
    except Exception as e:
        logger.error(f"조회 로그 저장 중 오류: {e}")

def get_stats() -> Dict:
    """데이터베이스 통계 반환"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 총 등록된 데이터 수
                cursor.execute('SELECT COUNT(*) as total FROM phone_data')
                total_records = cursor.fetchone()['total']
                
                # 유니크한 전화번호 수
                cursor.execute('SELECT COUNT(DISTINCT phone_number) as unique_count FROM phone_data')
                unique_phones = cursor.fetchone()['unique_count']
                
                # 총 조회 수
                cursor.execute('SELECT COUNT(*) as total FROM query_logs')
                total_queries = cursor.fetchone()['total']
                
                # 성공한 조회 수
                cursor.execute('SELECT COUNT(*) as found FROM query_logs WHERE results_count > 0')
                successful_queries = cursor.fetchone()['found']
                
                return {
                    'total_records': total_records,
                    'unique_phones': unique_phones,
                    'total_queries': total_queries,
                    'successful_queries': successful_queries,
                    'success_rate': round((successful_queries / total_queries * 100) if total_queries > 0 else 0, 2)
                }
    except Exception as e:
        logger.error(f"통계 조회 중 오류: {e}")
        return {}

def get_phone_summary() -> List[Dict]:
    """전화번호별 요약 정보 (중복 수 포함)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    SELECT phone_number, COUNT(*) as count, 
                           MIN(created_at) as first_added,
                           MAX(created_at) as last_added
                    FROM phone_data 
                    GROUP BY phone_number 
                    ORDER BY count DESC, last_added DESC
                ''')
                
                results = cursor.fetchall()
                return [dict(result) for result in results]
    except Exception as e:
        logger.error(f"요약 정보 조회 중 오류: {e}")
        return []

def bulk_insert_data(data_list: List[Dict]) -> int:
    """대량 데이터 삽입"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                # 배치 삽입을 위한 데이터 준비
                insert_data = [
                    (item['phone_number'], item['content'], item.get('created_at'))
                    for item in data_list
                ]
                
                cursor.executemany('''
                    INSERT INTO phone_data (phone_number, content, created_at)
                    VALUES (%s, %s, %s)
                ''', insert_data)
                
                conn.commit()
                inserted_count = cursor.rowcount
                logger.info(f"{inserted_count}개 레코드가 일괄 삽입되었습니다.")
                return inserted_count
                
    except Exception as e:
        logger.error(f"대량 삽입 중 오류: {e}")
        return 0