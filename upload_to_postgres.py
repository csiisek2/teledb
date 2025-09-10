#!/usr/bin/env python3
"""
CSV 데이터를 PostgreSQL에 업로드하는 스크립트
"""

import os
import csv
import psycopg
from dotenv import load_dotenv
import logging

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_csv_to_postgres():
    """CSV 데이터를 PostgreSQL에 업로드"""
    
    # PostgreSQL 연결
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        logger.error("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        return
    
    csv_file = './teledb_clean_export.csv'
    if not os.path.exists(csv_file):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    try:
        # PostgreSQL 연결
        logger.info("PostgreSQL 연결 중...")
        conn = psycopg.connect(DATABASE_URL)
        logger.info("PostgreSQL 연결 성공")
        
        with conn:
            with conn.cursor() as cursor:
                
                # 기존 데이터 확인
                cursor.execute("SELECT COUNT(*) FROM phone_data")
                existing_count = cursor.fetchone()[0]
                logger.info(f"기존 데이터: {existing_count}개")
                
                if existing_count > 0:
                    response = input(f"기존 데이터 {existing_count}개가 있습니다. 삭제하고 새로 업로드하시겠습니까? (y/N): ")
                    if response.lower() == 'y':
                        cursor.execute("DELETE FROM phone_data")
                        logger.info("기존 데이터 삭제 완료")
                    else:
                        logger.info("업로드 취소")
                        return
                
                # CSV 파일 읽기 및 업로드
                logger.info(f"CSV 파일 읽는 중: {csv_file}")
                
                upload_count = 0
                batch_size = 1000
                batch_data = []
                
                with open(csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    
                    for row in reader:
                        batch_data.append((
                            row['phone_number'],
                            row['content'],
                            row.get('created_at', 'NOW()')
                        ))
                        
                        # 배치 처리
                        if len(batch_data) >= batch_size:
                            cursor.executemany(
                                "INSERT INTO phone_data (phone_number, content, created_at) VALUES (%s, %s, %s)",
                                batch_data
                            )
                            upload_count += len(batch_data)
                            logger.info(f"업로드 진행: {upload_count}개")
                            batch_data = []
                    
                    # 남은 데이터 처리
                    if batch_data:
                        cursor.executemany(
                            "INSERT INTO phone_data (phone_number, content, created_at) VALUES (%s, %s, %s)",
                            batch_data
                        )
                        upload_count += len(batch_data)
                
                # 커밋
                conn.commit()
                logger.info(f"✅ 업로드 완료: 총 {upload_count}개 레코드")
                
                # 최종 확인
                cursor.execute("SELECT COUNT(*) FROM phone_data")
                final_count = cursor.fetchone()[0]
                logger.info(f"최종 데이터베이스 레코드 수: {final_count}개")
                
                # 샘플 데이터 확인
                cursor.execute("SELECT phone_number, content FROM phone_data LIMIT 5")
                samples = cursor.fetchall()
                logger.info("샘플 데이터:")
                for i, (phone, content) in enumerate(samples, 1):
                    logger.info(f"  {i}. {phone} - {content[:50]}...")
                
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        
if __name__ == "__main__":
    upload_csv_to_postgres()