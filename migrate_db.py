#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
기존 복잡한 구조를 단순한 phone_number + content 구조로 변경
"""

import sqlite3
import os
import sys
from datetime import datetime

def backup_existing_data(old_db_path):
    """기존 데이터 백업"""
    backup_data = []
    
    if not os.path.exists(old_db_path):
        print("기존 데이터베이스 파일이 없습니다.")
        return backup_data
    
    try:
        with sqlite3.connect(old_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM phone_data")
            
            for row in cursor.fetchall():
                # 기존 여러 필드를 content 하나로 합치기
                content_parts = []
                
                if row['name']:
                    content_parts.append(f"이름: {row['name']}")
                if row['company']:
                    content_parts.append(f"회사: {row['company']}")
                if row['address']:
                    content_parts.append(f"주소: {row['address']}")
                if row['email']:
                    content_parts.append(f"이메일: {row['email']}")
                if row['notes']:
                    content_parts.append(f"메모: {row['notes']}")
                
                content = " | ".join(content_parts) if content_parts else "정보 없음"
                
                backup_data.append({
                    'phone_number': row['phone_number'],
                    'content': content
                })
                
        print(f"기존 데이터 {len(backup_data)}개를 백업했습니다.")
        
    except sqlite3.Error as e:
        print(f"백업 중 오류: {e}")
    
    return backup_data

def create_new_database(db_path):
    """새로운 단순한 데이터베이스 구조 생성"""
    
    # 기존 파일 삭제 (백업은 이미 했음)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 단순한 테이블 구조: phone_number + content만
        cursor.execute('''
            CREATE TABLE phone_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 조회 로그 테이블 (단순화)
        cursor.execute('''
            CREATE TABLE query_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                query_phone TEXT,
                results_count INTEGER DEFAULT 0,
                query_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 인덱스 생성 (중복 허용)
        cursor.execute('CREATE INDEX idx_phone ON phone_data(phone_number)')
        
        conn.commit()
        print("새로운 데이터베이스 구조가 생성되었습니다.")

def migrate_data(backup_data, new_db_path):
    """백업 데이터를 새 구조로 마이그레이션"""
    
    with sqlite3.connect(new_db_path) as conn:
        cursor = conn.cursor()
        
        for data in backup_data:
            cursor.execute('''
                INSERT INTO phone_data (phone_number, content)
                VALUES (?, ?)
            ''', (data['phone_number'], data['content']))
        
        conn.commit()
        print(f"데이터 {len(backup_data)}개가 마이그레이션되었습니다.")

def main():
    """메인 마이그레이션 실행"""
    old_db = './teledb.sqlite'
    new_db = './teledb_new.sqlite'
    
    print("🔄 데이터베이스 마이그레이션 시작...")
    print("=" * 50)
    
    # 1. 기존 데이터 백업
    print("1. 기존 데이터 백업 중...")
    backup_data = backup_existing_data(old_db)
    
    # 2. 새 데이터베이스 구조 생성
    print("\n2. 새 데이터베이스 구조 생성 중...")
    create_new_database(new_db)
    
    # 3. 데이터 마이그레이션
    print("\n3. 데이터 마이그레이션 중...")
    migrate_data(backup_data, new_db)
    
    # 4. 파일 교체
    print("\n4. 파일 교체 중...")
    if os.path.exists(old_db):
        os.rename(old_db, f'./teledb_old_{int(datetime.now().timestamp())}.sqlite')
    os.rename(new_db, old_db)
    
    print("\n✅ 마이그레이션 완료!")
    print("=" * 50)
    print("새로운 구조:")
    print("- phone_number: 전화번호 (중복 허용)")
    print("- content: 모든 정보를 하나의 텍스트로")
    print("- 중복 번호 조회시 모든 내용 표시")

if __name__ == '__main__':
    main()