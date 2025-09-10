"""
유틸리티 함수들
"""

import os
import re
from typing import Dict

def is_admin(user_id: int) -> bool:
    """사용자가 관리자인지 확인"""
    admin_user_id = int(os.getenv('ADMIN_USER_ID', 0))
    return user_id == admin_user_id

def validate_phone_number(phone_number: str) -> bool:
    """전화번호 형식 검증"""
    # 한국 휴대폰 번호 패턴
    # 010으로 시작하는 11자리 또는 011,016,017,018,019로 시작하는 10-11자리
    if phone_number.startswith('010'):
        pattern = r'^010\d{8}$'  # 11자리 고정
    else:
        pattern = r'^(011|016|017|018|019)\d{7,8}$'  # 10-11자리
    
    return bool(re.match(pattern, phone_number))

def format_phone_number(phone_number: str) -> str:
    """전화번호를 표시용으로 포맷팅"""
    if len(phone_number) == 11 and phone_number.startswith('010'):
        return f"{phone_number[:3]}-{phone_number[3:7]}-{phone_number[7:]}"
    elif len(phone_number) == 10:
        return f"{phone_number[:3]}-{phone_number[3:6]}-{phone_number[6:]}"
    return phone_number

def format_phone_info(data: Dict) -> str:
    """단순화된 전화번호 정보 포맷팅"""
    lines = []
    
    # 전화번호
    if data.get('phone_number'):
        formatted_phone = format_phone_number(data['phone_number'])
        lines.append(f"📱 **전화번호:** `{formatted_phone}`")
    
    # 내용
    if data.get('content'):
        lines.append(f"📝 **내용:** {data['content']}")
    
    # 등록일
    if data.get('created_at'):
        lines.append(f"📅 **등록일:** {data['created_at'][:19]}")
    
    return '\n'.join(lines) if lines else "정보가 없습니다."

def clean_phone_number(phone_number: str) -> str:
    """전화번호에서 하이픈, 공백 등 제거"""
    return re.sub(r'[^0-9]', '', phone_number)

def parse_add_data(text: str) -> Dict:
    """단순화된 추가 명령어 데이터 파싱"""
    parts = text.split(' ', 1)  # 첫 번째 공백으로만 분리
    
    result = {}
    
    if len(parts) >= 1:
        result['phone_number'] = clean_phone_number(parts[0].strip())
    if len(parts) >= 2:
        result['content'] = parts[1].strip()
    
    return result

def truncate_text(text: str, max_length: int = 100) -> str:
    """텍스트를 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."