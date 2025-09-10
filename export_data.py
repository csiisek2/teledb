#!/usr/bin/env python3
"""
SQLite 데이터를 CSV로 내보내는 스크립트
"""

import sqlite3
import csv
import os

def export_phone_data():
    """전화번호 데이터를 CSV로 내보내기"""
    
    # 데이터베이스 연결
    db_path = './teledb.sqlite'
    if not os.path.exists(db_path):
        print("❌ SQLite 데이터베이스 파일을 찾을 수 없습니다.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 데이터 조회
        cursor.execute("""
            SELECT phone_number, content, created_at 
            FROM phone_data 
            ORDER BY created_at
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 데이터베이스에 데이터가 없습니다.")
            return
        
        # CSV로 내보내기
        csv_filename = 'teledb_export.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # 헤더 쓰기
            writer.writerow(['phone_number', 'content', 'created_at'])
            
            # 데이터 쓰기
            for row in rows:
                writer.writerow(row)
        
        print(f"✅ {len(rows)}개 레코드를 {csv_filename}으로 내보냈습니다.")
        
        # 샘플 데이터 표시
        print("\n📊 샘플 데이터:")
        for i, row in enumerate(rows[:5]):
            phone, content, created = row
            print(f"   {i+1}. {phone} - {content[:50]}...")
            
        if len(rows) > 5:
            print(f"   ... 외 {len(rows)-5}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    export_phone_data()