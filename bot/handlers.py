"""
단순화된 텔레그램 봇 명령어 핸들러
구조: phone_number + content (중복 허용)
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from .database_postgres import search_phone, add_phone_data, update_phone_data, delete_phone_data, log_query, get_stats, get_phone_summary
from .utils import is_admin, validate_phone_number, format_phone_number, clean_phone_number
from .security import check_user_access, SecurityManager

# 관리자 모드 상태 저장
admin_mode_users = set()

# 허용된 슈퍼어드민 username (보안 강화)
SUPER_ADMIN_USERNAME = "dis7414"  # 오직 이 username만 superadmin 사용 가능

# 관리자가 허용한 사용자 목록 (동적 관리)
approved_users = set()
# 관리자 권한을 가진 사용자 목록
admin_users = set()

# dis7414는 자동으로 승인됨 (슈퍼어드민)
approved_users.add("dis7414")
admin_users.add("dis7414")

# 사용자 승인 요청 명령어
async def approve_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자 승인 명령어 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **사용자 승인 명령어:**\n\n"
            "• `/approve @username` - 사용자 승인\n"
            "• `/approve 123456789` - 사용자 ID로 승인\n"
            "• `/disapprove @username` - 승인 취소\n"
            "• `/users` - 승인된 사용자 목록\n\n"
            "예시: `/approve @john123`",
            parse_mode='Markdown'
        )
        return
    
    user_input = context.args[0].strip()
    
    # @username 형태면 @제거
    if user_input.startswith('@'):
        username = user_input[1:]
        approved_users.add(username)
        await update.message.reply_text(f"✅ 사용자 `@{username}` 승인 완료!")
    else:
        # 숫자면 user_id로 처리
        try:
            user_id = int(user_input)
            approved_users.add(user_id)
            await update.message.reply_text(f"✅ 사용자 ID `{user_id}` 승인 완료!")
        except:
            await update.message.reply_text("❌ 올바른 username 또는 user_id를 입력하세요.")

async def disapprove_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자 승인 취소 명령어 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text("사용법: `/disapprove @username` 또는 `/disapprove user_id`")
        return
    
    user_input = context.args[0].strip()
    
    # @username 형태면 @제거
    if user_input.startswith('@'):
        username = user_input[1:]
        if username in approved_users:
            approved_users.remove(username)
            await update.message.reply_text(f"❌ 사용자 `@{username}` 승인 취소됨")
        else:
            await update.message.reply_text(f"❓ `@{username}`는 승인되지 않은 사용자입니다.")
    else:
        try:
            user_id = int(user_input)
            if user_id in approved_users:
                approved_users.remove(user_id)
                await update.message.reply_text(f"❌ 사용자 ID `{user_id}` 승인 취소됨")
            else:
                await update.message.reply_text(f"❓ `{user_id}`는 승인되지 않은 사용자입니다.")
        except:
            await update.message.reply_text("❌ 올바른 username 또는 user_id를 입력하세요.")

async def admin_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 권한 부여 명령어 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 **관리자 권한 부여:**\n\n"
            "• `/admin @username` - 관리자 권한 부여\n"
            "• `/unadmin @username` - 관리자 권한 취소\n"
            "• `/admins` - 관리자 목록\n\n"
            "예시: `/admin @john123`",
            parse_mode='Markdown'
        )
        return
    
    user_input = context.args[0].strip()
    
    # @username 형태면 @제거
    if user_input.startswith('@'):
        username = user_input[1:]
        admin_users.add(username)
        approved_users.add(username)  # 관리자는 자동으로 봇 사용도 허가
        await update.message.reply_text(f"🔑 사용자 `@{username}` 관리자 권한 부여 완료!")
    else:
        # 숫자면 user_id로 처리
        try:
            user_id = int(user_input)
            admin_users.add(user_id)
            approved_users.add(user_id)  # 관리자는 자동으로 봇 사용도 허가
            await update.message.reply_text(f"🔑 사용자 ID `{user_id}` 관리자 권한 부여 완료!")
        except:
            await update.message.reply_text("❌ 올바른 username 또는 user_id를 입력하세요.")

async def unadmin_user_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 권한 취소 명령어 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text("사용법: `/unadmin @username` 또는 `/unadmin user_id`")
        return
    
    user_input = context.args[0].strip()
    
    # @username 형태면 @제거
    if user_input.startswith('@'):
        username = user_input[1:]
        if username in admin_users:
            admin_users.remove(username)
            await update.message.reply_text(f"❌ 사용자 `@{username}` 관리자 권한 취소됨")
        else:
            await update.message.reply_text(f"❓ `@{username}`는 관리자가 아닙니다.")
    else:
        try:
            user_id = int(user_input)
            if user_id in admin_users:
                admin_users.remove(user_id)
                await update.message.reply_text(f"❌ 사용자 ID `{user_id}` 관리자 권한 취소됨")
            else:
                await update.message.reply_text(f"❓ `{user_id}`는 관리자가 아닙니다.")
        except:
            await update.message.reply_text("❌ 올바른 username 또는 user_id를 입력하세요.")

async def list_admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 목록 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not admin_users:
        await update.message.reply_text("📭 관리자가 없습니다.")
        return
    
    user_list = []
    for i, user_item in enumerate(admin_users, 1):
        if isinstance(user_item, str):
            user_list.append(f"{i}. @{user_item}")
        else:
            user_list.append(f"{i}. ID: {user_item}")
    
    response = f"🔑 **관리자 목록** ({len(admin_users)}명)\n\n"
    response += "\n".join(user_list)
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """승인된 사용자 목록 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # dis7414만 사용 가능
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not approved_users:
        await update.message.reply_text("📭 승인된 사용자가 없습니다.")
        return
    
    user_list = []
    for i, user_item in enumerate(approved_users, 1):
        if isinstance(user_item, str):
            user_list.append(f"{i}. @{user_item}")
        else:
            user_list.append(f"{i}. ID: {user_item}")
    
    response = f"👥 **승인된 사용자 목록** ({len(approved_users)}명)\n\n"
    response += "\n".join(user_list)
    
    await update.message.reply_text(response, parse_mode='Markdown')

# 비밀 관리자 모드 진입 명령어
async def secret_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """비밀 관리자 모드 진입 (특정 username만 가능)"""
    user = update.effective_user
    
    # username 체크 (보안 강화)
    if not user.username or user.username != SUPER_ADMIN_USERNAME:
        # 허용되지 않은 사용자면 일반 메시지처럼 처리
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    # 추가적으로 관리자 ID도 체크 (이중 보안)
    if not is_admin(user.id):
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    # 관리자 모드 토글
    if user.id in admin_mode_users:
        admin_mode_users.remove(user.id)
        await update.message.reply_text("👋 관리자 모드가 종료되었습니다.")
    else:
        admin_mode_users.add(user.id)
        
        # 메시지 즉시 삭제 후 개인 메시지로 안내
        try:
            await update.message.delete()  # 명령어 메시지 삭제
        except:
            pass  # 삭제 실패해도 계속 진행
        
        await update.message.reply_text(
            "🔑 **관리자 모드 실행중** (메시지는 곧 삭제됩니다)\n\n"
            "📝 **보안 모드:**\n"
            "• 모든 입력은 즉시 삭제처리\n"
            "• 결과만 개인메시지로 전송\n\n"
            "💡 **사용법:**\n"
            "• `번호 내용` = 추가\n"
            "• `번호 del` = 삭제\n"
            "• `/sa` = 모드 종료",
            parse_mode='Markdown'
        )

async def exit_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 모드 종료"""
    user = update.effective_user
    
    if user.id in admin_mode_users:
        admin_mode_users.remove(user.id)
        await update.message.reply_text("👋 관리자 모드를 종료했습니다.")
    else:
        await update.message.reply_text("❌ 관리자 모드가 활성화되어 있지 않습니다.")

# 인증 명령어 추가
async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """패스워드 인증 명령어"""
    user = update.effective_user
    
    if not context.args:
        await update.message.reply_text(
            "🔐 인증을 위해 패스워드를 입력하세요.\n"
            "예: `/auth 패스워드`",
            parse_mode='Markdown'
        )
        return
    
    password = ' '.join(context.args)
    
    if SecurityManager.authenticate_user(user.id, password):
        await update.message.reply_text("✅ 인증되었습니다! 이제 봇을 사용할 수 있습니다.")
    else:
        await update.message.reply_text("❌ 잘못된 패스워드입니다.")

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """로그아웃 명령어"""
    user = update.effective_user
    SecurityManager.logout_user(user.id)
    await update.message.reply_text("👋 로그아웃되었습니다.")

async def security_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """보안 정보 명령어 (관리자 전용)"""
    user = update.effective_user
    
    # 슈퍼어드민이거나 관리자 권한이 있는지 확인
    if not (is_admin(user.id) or user.username in admin_users or user.id in admin_users):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    info = SecurityManager.get_security_info()
    response = f"🔐 **보안 설정 정보**\n\n{info}"
    
    await update.message.reply_text(response, parse_mode='Markdown')

logger = logging.getLogger(__name__)

# 관리자 사용자 ID
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    user = update.effective_user
    welcome_text = f"""🔍 **TeleDB - 전화번호 조회 시스템**

안녕하세요, {user.first_name}님!

📱 **사용 방법:**
• `01012345678` - 전화번호 바로 입력하여 조회

💡 **간편 조회**: 전화번호만 입력하면 바로 검색됩니다!"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어"""
    help_text = """📖 **TeleDB 사용 가이드**

🔍 **사용법:**
전화번호만 입력하세요. 예: `01012345678`

📝 **형식:**
• 하이픈 자동 제거: 010-1234-5678 → 01012345678  
• 여러 정보가 있으면 모두 표시됩니다."""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전화번호 조회 명령어 - 모든 매칭 결과 표시"""
    user = update.effective_user
    
    # 사용자 허가 체크 (간소화)
    if user.username not in approved_users and user.id not in approved_users:
        await update.message.reply_text(
            "⛔ **허용된 사용자가 아닙니다.**\n\n"
            "📞 관리자에게 문의하세요.",
            parse_mode='Markdown'
        )
        return
    
    if not context.args:
        await update.message.reply_text("❌ 전화번호를 입력해주세요.\n예: `/search 01012345678`", parse_mode='Markdown')
        return
    
    phone_number = clean_phone_number(context.args[0].strip())
    
    # 전화번호 형식 검증
    if not validate_phone_number(phone_number):
        await update.message.reply_text("❌ 올바른 전화번호 형식이 아닙니다.\n예: `01012345678`", parse_mode='Markdown')
        return
    
    # 데이터베이스에서 모든 매칭 정보 조회
    results = search_phone(phone_number)
    
    # 조회 기록 저장 (보안 + 통계)
    SecurityManager.record_query(user.id)
    log_query(user.id, user.username or user.first_name, phone_number, len(results))
    
    if results:
        # 전화번호 포맷팅
        formatted_phone = format_phone_number(phone_number)
        
        response = f"✅ **조회 결과: `{formatted_phone}`**\n\n"
        response += f"📊 **총 {len(results)}개의 정보를 찾았습니다.**\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"**{i}. {result['content']}**\n"
            response += f"   📅 등록일: {result['created_at'][:19]}\n\n"
        
        response += "🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*"
        
        sent_msg = await update.message.reply_text(response, parse_mode='Markdown')
        # 30초 후 자동 삭제
        import asyncio
        asyncio.create_task(delete_message_after_delay(sent_msg, 30))
    else:
        formatted_phone = format_phone_number(phone_number)
        sent_msg = await update.message.reply_text(f"❌ 전화번호 `{formatted_phone}`에 대한 정보를 찾을 수 없습니다.\n\n🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*", parse_mode='Markdown')
        # 30초 후 자동 삭제
        import asyncio
        asyncio.create_task(delete_message_after_delay(sent_msg, 30))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """통계 명령어"""
    user = update.effective_user
    
    # 사용자 허가 체크 (간소화)
    if user.username not in approved_users and user.id not in approved_users:
        await update.message.reply_text(
            "⛔ **허용된 사용자가 아닙니다.**\n\n"
            "📞 관리자에게 문의하세요.",
            parse_mode='Markdown'
        )
        return
    
    stats = get_stats()
    
    stats_text = f"""
📊 **TeleDB 통계**

📋 총 등록된 데이터: **{stats['total_records']:,}개**
📱 유니크 전화번호: **{stats['unique_phones']:,}개**
🔍 총 조회 횟수: **{stats['total_queries']:,}회**
✅ 성공한 조회: **{stats['successful_queries']:,}회**
📈 조회 성공률: **{stats['success_rate']}%**

💡 평균 {stats['total_records'] / max(stats['unique_phones'], 1):.1f}개의 정보가 번호당 등록됨
"""
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """정보 추가 명령어 (관리자 전용) - 중복 허용"""
    user = update.effective_user
    
    # 슈퍼어드민이거나 관리자 권한이 있는지 확인
    if not (is_admin(user.id) or user.username in admin_users or user.id in admin_users):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ 올바른 형식으로 입력해주세요.\n"
            "예: `/add 01012345678 홍길동 | 삼성전자 | 서울시 강남구`",
            parse_mode='Markdown'
        )
        return
    
    # 전화번호와 내용 분리
    phone_number = clean_phone_number(context.args[0].strip())
    content = ' '.join(context.args[1:]).strip()
    
    # 전화번호 형식 검증
    if not validate_phone_number(phone_number):
        await update.message.reply_text("❌ 올바른 전화번호 형식이 아닙니다.")
        return
    
    # 데이터베이스에 추가 (중복 허용)
    success = add_phone_data(phone_number, content)
    
    if success:
        formatted_phone = format_phone_number(phone_number)
        await update.message.reply_text(f"✅ 전화번호 `{formatted_phone}`에 정보가 성공적으로 추가되었습니다.\n📝 내용: {content}", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ 데이터 추가 중 오류가 발생했습니다.")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """정보 삭제 명령어 (관리자 전용) - 해당 번호의 모든 정보 삭제"""
    user = update.effective_user
    
    # 슈퍼어드민이거나 관리자 권한이 있는지 확인
    if not (is_admin(user.id) or user.username in admin_users or user.id in admin_users):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ 삭제할 전화번호를 입력해주세요.\n예: `/delete 01012345678`", parse_mode='Markdown')
        return
    
    phone_number = clean_phone_number(context.args[0].strip())
    
    # 전화번호 형식 검증
    if not validate_phone_number(phone_number):
        await update.message.reply_text("❌ 올바른 전화번호 형식이 아닙니다.")
        return
    
    # 삭제 전 확인
    results = search_phone(phone_number)
    if not results:
        formatted_phone = format_phone_number(phone_number)
        await update.message.reply_text(f"❌ 전화번호 `{formatted_phone}`를 찾을 수 없습니다.", parse_mode='Markdown')
        return
    
    # 데이터베이스에서 모든 정보 삭제
    success = delete_phone_data(phone_number)
    
    if success:
        formatted_phone = format_phone_number(phone_number)
        await update.message.reply_text(f"✅ 전화번호 `{formatted_phone}`의 모든 정보({len(results)}개)가 성공적으로 삭제되었습니다.", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ 데이터 삭제 중 오류가 발생했습니다.")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전화번호 목록 명령어 (관리자 전용)"""
    user = update.effective_user
    
    # 슈퍼어드민이거나 관리자 권한이 있는지 확인
    if not (is_admin(user.id) or user.username in admin_users or user.id in admin_users):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    summary = get_phone_summary()
    
    if not summary:
        await update.message.reply_text("📭 등록된 전화번호가 없습니다.")
        return
    
    response = "📋 **등록된 전화번호 목록**\n\n"
    
    # 처음 20개만 표시
    for i, item in enumerate(summary[:20], 1):
        formatted_phone = format_phone_number(item['phone_number'])
        response += f"**{i}. `{formatted_phone}`**\n"
        response += f"   📊 {item['count']}개 정보\n"
        response += f"   📅 최근: {item['last_added'][:19]}\n\n"
    
    if len(summary) > 20:
        response += f"... 외 {len(summary) - 20}개 번호\n\n"
    
    response += f"📊 **총 {len(summary)}개의 전화번호**"
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def bulk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """대량 데이터 추가 명령어 (관리자 전용) - 중복 허용"""
    user = update.effective_user
    
    # 슈퍼어드민이거나 관리자 권한이 있는지 확인
    if not (is_admin(user.id) or user.username in admin_users or user.id in admin_users):
        await update.message.reply_text("❌ 관리자만 사용할 수 있는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ 대량 추가 형식:\n"
            "`/bulk 전화번호1 내용1, 전화번호2 내용2`\n\n"
            "예시:\n"
            "`/bulk 01011111111 김철수|A회사, 01022222222 이영희|B회사`",
            parse_mode='Markdown'
        )
        return
    
    # 데이터 파싱
    bulk_data = ' '.join(context.args)
    entries = [entry.strip() for entry in bulk_data.split(',')]
    
    success_count = 0
    error_count = 0
    results = []
    
    for i, entry in enumerate(entries, 1):
        try:
            parts = entry.split(' ', 1)  # 첫 번째 공백으로만 분리
            if len(parts) < 2:
                results.append(f"❌ 항목 {i}: 형식 오류 (전화번호 내용)")
                error_count += 1
                continue
            
            phone_number = clean_phone_number(parts[0].strip())
            content = parts[1].strip()
            
            # 전화번호 검증
            if not validate_phone_number(phone_number):
                results.append(f"❌ 항목 {i}: 잘못된 전화번호 `{phone_number}`")
                error_count += 1
                continue
            
            # 데이터베이스에 추가 (중복 허용)
            result = add_phone_data(phone_number, content)
            
            if result:
                formatted_phone = format_phone_number(phone_number)
                results.append(f"✅ 항목 {i}: `{formatted_phone}` 추가 성공")
                success_count += 1
            else:
                results.append(f"❌ 항목 {i}: `{phone_number}` 추가 실패")
                error_count += 1
                
        except Exception as e:
            results.append(f"❌ 항목 {i}: 오류 - {str(e)}")
            error_count += 1
    
    # 결과 요약
    summary = f"📊 **대량 추가 완료**\n\n"
    summary += f"✅ 성공: {success_count}개\n"
    summary += f"❌ 실패: {error_count}개\n\n"
    
    # 상세 결과 (처음 10개만 표시)
    if results:
        summary += "📋 **상세 결과:**\n"
        for result in results[:10]:
            summary += f"{result}\n"
        
        if len(results) > 10:
            summary += f"\n... 외 {len(results) - 10}개 항목"
    
    await update.message.reply_text(summary, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 메시지 처리"""
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # 슈퍼어드민 모드에서 간단 명령어 처리
    if user.id in admin_mode_users and user.username == SUPER_ADMIN_USERNAME:
        parts = message_text.split(' ', 1)
        if len(parts) == 2:
            phone_part = parts[0].strip()
            content_part = parts[1].strip()
            
            # 전화번호인지 확인
            phone_number = clean_phone_number(phone_part)
            if validate_phone_number(phone_number):
                # 원본 메시지 즉시 삭제 (보안)
                try:
                    await update.message.delete()
                except:
                    pass
                
                if content_part == "d" or content_part == "del" or content_part == "삭제":
                    # 삭제 명령어 (더 간단한 "d" 추가)
                    results = search_phone(phone_number)
                    if results:
                        success = delete_phone_data(phone_number)
                        if success:
                            formatted_phone = format_phone_number(phone_number)
                            sent_msg = await update.message.reply_text(f"✅ 삭제 성공!\n🗑️ `{formatted_phone}` 삭제완료 ({len(results)}개) - 5초후삭제", parse_mode='Markdown')
                            import asyncio
                            asyncio.create_task(delete_message_after_delay(sent_msg, 5))
                        else:
                            await update.message.reply_text("❌ 삭제 실패")
                    else:
                        formatted_phone = format_phone_number(phone_number)
                        await update.message.reply_text(f"❌ `{formatted_phone}` 없음", parse_mode='Markdown')
                    return
                else:
                    # 추가 명령어
                    success = add_phone_data(phone_number, content_part)
                    if success:
                        formatted_phone = format_phone_number(phone_number)
                        sent_msg = await update.message.reply_text(f"✅ 추가 성공!\n📱 `{formatted_phone}` 추가완료 - 5초후삭제\n📝 {content_part[:20]}{'...' if len(content_part) > 20 else ''}", parse_mode='Markdown')
                        import asyncio
                        asyncio.create_task(delete_message_after_delay(sent_msg, 5))
                    else:
                        await update.message.reply_text("❌ 추가 실패")
                    return
    
    # 전화번호 패턴인지 확인
    cleaned_phone = clean_phone_number(message_text)
    is_valid = validate_phone_number(cleaned_phone)
    
    if is_valid:
        # 사용자 허가 체크 (간소화)
        if user.username not in approved_users and user.id not in approved_users:
            await update.message.reply_text(
                "⛔ **허용된 사용자가 아닙니다.**\n\n"
                "📞 관리자에게 문의하세요.",
                parse_mode='Markdown'
            )
            return
        
        # 전화번호 조회
        results = search_phone(cleaned_phone)
        
        if results:
            formatted_phone = format_phone_number(cleaned_phone)
            response = f"✅ **조회 결과: `{formatted_phone}`**\n\n"
            response += f"📊 **총 {len(results)}개의 정보:**\n\n"
            
            for i, result in enumerate(results, 1):
                response += f"**{i}. {result['content']}**\n"
                response += f"   📅 등록일: {result['created_at'][:19]}\n\n"
            
            response += "🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*"
            
            sent_msg = await update.message.reply_text(response, parse_mode='Markdown')
            # 응답 메시지와 사용자 입력 메시지 모두 30초 후 자동 삭제
            import asyncio
            asyncio.create_task(delete_message_after_delay(sent_msg, 30))
            # 그룹과 1대1 모두에서 사용자 입력 메시지 삭제
            asyncio.create_task(delete_message_after_delay(update.message, 30))
        else:
            formatted_phone = format_phone_number(cleaned_phone)
            sent_msg = await update.message.reply_text(f"❌ 전화번호 `{formatted_phone}`에 대한 정보를 찾을 수 없습니다.\n\n🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*", parse_mode='Markdown')
            # 응답 메시지와 사용자 입력 메시지 모두 30초 후 자동 삭제
            import asyncio
            asyncio.create_task(delete_message_after_delay(sent_msg, 30))
            # 그룹과 1대1 모두에서 사용자 입력 메시지 삭제
            asyncio.create_task(delete_message_after_delay(update.message, 30))
    else:
        await update.message.reply_text("❓ 전화번호를 입력해주세요. 예: `01012345678`", parse_mode='Markdown')

# 메시지 자동 삭제 함수
async def delete_message_after_delay(message, delay_seconds):
    """지정된 시간 후 메시지 삭제"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except:
        pass

def setup_handlers(application):
    """핸들러 설정"""
    # 명령어 핸들러
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("bulk", bulk_command))
    
    # 보안 관련 핸들러
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("security", security_info_command))
    
    # 비밀 관리자 모드 핸들러 (짧은 명령어)
    application.add_handler(CommandHandler("sa", secret_admin_command))  # /sa로 간단하게
    application.add_handler(CommandHandler("superadmin", secret_admin_command))  # 기존 명령어도 유지
    application.add_handler(CommandHandler("exit_admin", exit_admin_command))
    
    # 사용자 승인 관련 핸들러 (dis7414 전용) - 영어 명령어만 사용
    application.add_handler(CommandHandler("approve", approve_user_command))
    application.add_handler(CommandHandler("disapprove", disapprove_user_command))
    application.add_handler(CommandHandler("users", list_users_command))
    
    # 관리자 권한 관련 핸들러 (dis7414 전용)
    application.add_handler(CommandHandler("admin", admin_user_command))
    application.add_handler(CommandHandler("unadmin", unadmin_user_command))
    application.add_handler(CommandHandler("admins", list_admins_command))
    
    # 일반 메시지 핸들러
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("모든 핸들러가 설정되었습니다.")