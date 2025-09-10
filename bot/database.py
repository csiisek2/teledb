"""
단순화된 데이터베이스 연결 및 쿼리 처리
구조: phone_number + content (중복 허용)
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로
DATABASE_PATH = os.getenv('DATABASE_PATH', './teledb.sqlite')

def get_connection():
    """데이터베이스 연결 반환"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn

def init_database():
    """데이터베이스 테이블 초기화"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 단순한 전화번호 정보 테이블 (중복 허용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phone_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 조회 로그 테이블 (단순화)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                query_phone TEXT,
                results_count INTEGER DEFAULT 0,
                query_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성 (중복 허용)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON phone_data(phone_number)')
        
        conn.commit()
        logger.info("데이터베이스 테이블이 초기화되었습니다.")

def search_phone(phone_number: str) -> List[Dict]:
    """전화번호로 모든 매칭 정보 조회 (중복 허용)"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM phone_data 
            WHERE phone_number = ?
            ORDER BY created_at DESC
        ''', (phone_number,))
        
        results = cursor.fetchall()
        return [dict(result) for result in results] if results else []

def add_phone_data(phone_number: str, content: str) -> bool:
    """새 전화번호 정보 추가 (중복 허용)"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO phone_data (phone_number, content)
                VALUES (?, ?)
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
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE phone_data 
                SET content = ?
                WHERE phone_number = ? AND content = ?
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
            cursor = conn.cursor()
            
            if content:
                # 특정 내용만 삭제
                cursor.execute('DELETE FROM phone_data WHERE phone_number = ? AND content = ?', 
                              (phone_number, content))
            else:
                # 해당 번호의 모든 내용 삭제
                cursor.execute('DELETE FROM phone_data WHERE phone_number = ?', (phone_number,))
            
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
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_logs (user_id, username, query_phone, results_count)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, query_phone, results_count))
            conn.commit()
    except Exception as e:
        logger.error(f"조회 로그 저장 중 오류: {e}")

def get_stats() -> Dict:
    """데이터베이스 통계 반환"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
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

def get_phone_summary() -> List[Dict]:
    """전화번호별 요약 정보 (중복 수 포함)"""
    with get_connection() as conn:
        cursor = conn.cursor()
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