#!/usr/bin/env python3
"""
중복 제거하고 원본 데이터만 추출하는 스크립트
"""

import sqlite3
import csv
import os

def clean_export():
    """중복 제거하고 원본 데이터만 CSV로 내보내기"""
    
    # 데이터베이스 연결
    db_path = './teledb.sqlite'
    if not os.path.exists(db_path):
        print("❌ SQLite 데이터베이스 파일을 찾을 수 없습니다.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 중복 제거하고 가장 오래된 레코드만 선택
        cursor.execute("""
            SELECT phone_number, content, MIN(created_at) as created_at
            FROM phone_data 
            WHERE content NOT LIKE '%바보%' 
            AND content NOT LIKE '%test%'
            AND content NOT LIKE '%테스트%'
            AND length(phone_number) = 11
            AND phone_number LIKE '010%'
            GROUP BY phone_number
            ORDER BY created_at
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("📭 정리된 데이터가 없습니다.")
            return
        
        # CSV로 내보내기
        csv_filename = 'teledb_clean_export.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # 헤더 쓰기
            writer.writerow(['phone_number', 'content', 'created_at'])
            
            # 데이터 쓰기
            for row in rows:
                writer.writerow(row)
        
        print(f"✅ 중복 제거 완료: {len(rows)}개 고유 레코드를 {csv_filename}으로 내보냈습니다.")
        
        # 샘플 데이터 표시
        print("\n📊 정리된 샘플 데이터:")
        for i, row in enumerate(rows[:5]):
            phone, content, created = row
            print(f"   {i+1}. {phone} - {content[:60]}...")
            
        if len(rows) > 5:
            print(f"   ... 외 {len(rows)-5}개")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    clean_export()