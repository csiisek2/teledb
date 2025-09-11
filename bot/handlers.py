"""
단순화된 텔레그램 봇 명령어 핸들러
구조: phone_number + content (중복 허용)
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .database_postgres import search_phone, add_phone_data, update_phone_data, delete_phone_data, log_query, get_stats, get_phone_summary
from .utils import is_admin, validate_phone_number, format_phone_number, clean_phone_number
from .security import check_user_access, SecurityManager

# 관리자 모드 상태 저장
admin_mode_users = set()

# 허용된 슈퍼어드민 username (보안 강화)
SUPER_ADMIN_USERNAME = "dis7414"  # 오직 이 username만 superadmin 사용 가능

# 비밀번호 기반 인증 시스템
ACCESS_PASSWORD = "seo09081!!"  # 봇 사용 비밀번호
authenticated_users = set()  # 인증된 사용자 목록 (user_id로 저장)

# 관리자 모드용 (슈퍼어드민)
SUPER_ADMIN_USER_ID = 5773319399  # dis7414의 user_id
admin_users = {SUPER_ADMIN_USER_ID}

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

async def sa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 모드 활성화 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    # 슈퍼어드민만 사용 가능
    if user.id != SUPER_ADMIN_USER_ID:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if user.id in admin_mode_users:
        admin_mode_users.remove(user.id)
        await update.message.reply_text("🔴 **관리자 모드 비활성화**\n일반 사용자 모드로 전환됩니다.", parse_mode='Markdown')
    else:
        admin_mode_users.add(user.id)
        await update.message.reply_text("🟢 **관리자 모드 활성화**\n\n📝 **간단 명령어:**\n• `전화번호 내용` - 정보 추가\n• `전화번호 d` - 정보 삭제\n• `/비번변경 새비밀번호` - 비밀번호 변경\n\n⚡ **예시:** `01012345678 홍길동`", parse_mode='Markdown')

async def changepass_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """비밀번호 변경 명령어 (슈퍼어드민 전용)"""
    global ACCESS_PASSWORD
    user = update.effective_user
    
    # 슈퍼어드민만 사용 가능
    if user.id != SUPER_ADMIN_USER_ID:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔐 **비밀번호 변경**\n\n"
            f"**현재 비밀번호:** `{ACCESS_PASSWORD}`\n\n"
            "**사용법:** `/비번변경 새비밀번호`\n"
            "**예시:** `/비번변경 newpass123`",
            parse_mode='Markdown'
        )
        return
    
    new_password = ' '.join(context.args).strip()
    
    # 비밀번호 검증
    if len(new_password) < 3:
        await update.message.reply_text("❌ 비밀번호는 최소 3자 이상이어야 합니다.")
        return
    
    if new_password == ACCESS_PASSWORD:
        await update.message.reply_text("❌ 현재 비밀번호와 동일합니다.")
        return
    
    old_password = ACCESS_PASSWORD
    ACCESS_PASSWORD = new_password
    
    # 입력 메시지 삭제 (보안)
    try:
        await update.message.delete()
    except:
        pass
    
    success_text = f"""✅ **비밀번호 변경 완료!**

**이전:** `{old_password}`
**새 비밀번호:** `{new_password}`

🔒 새로운 사용자들은 새 비밀번호를 사용해야 합니다.
📝 기존 인증된 사용자들은 그대로 유지됩니다.

⚠️ **이 메시지는 10초 후 자동 삭제됩니다.**"""
    
    sent_msg = await update.message.reply_text(success_text, parse_mode='Markdown')
    
    # 10초 후 삭제
    import asyncio
    asyncio.create_task(delete_message_after_delay(sent_msg, 10))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어 - 비밀번호 인증"""
    user = update.effective_user
    
    # 이미 인증된 사용자인지 확인
    if user.id in authenticated_users:
        welcome_text = f"""✅ **이미 인증됨** - TeleDB 사용 가능!

안녕하세요, {user.first_name}님!

📱 **사용 방법:**
• `01012345678` - 전화번호 바로 입력하여 조회
• `/help` - 도움말 보기

💡 **간편 조회**: 전화번호만 입력하면 바로 검색됩니다!"""
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        return
    
    # 간단한 거부 메시지만 표시
    auth_text = f"""⛔ **허용된 사용자가 아닙니다.**

🔐 **비밀번호를 입력하세요.**

📞 관리자에게 문의하세요."""
    
    await update.message.reply_text(auth_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """도움말 명령어"""
    user = update.effective_user
    
    # 비밀번호 인증 확인
    if user.id not in authenticated_users:
        await update.message.reply_text(
            "⛔ **허용된 사용자가 아닙니다.**\n\n"
            "🔐 **비밀번호를 입력하세요.**\n\n"
            "📞 관리자에게 문의하세요."
        )
        return
    
    help_text = """📖 **TeleDB 사용 가이드**

🔍 **사용법:**
전화번호만 입력하세요. 예: `01012345678`

📝 **형식:**
• 하이픈 자동 제거: 010-1234-5678 → 01012345678  
• 여러 정보가 있으면 모두 표시됩니다.

📊 **추가 명령어:**
• `/stats` - 데이터베이스 통계 보기

🔒 **보안:** 모든 조회 메시지는 30초 후 자동 삭제됩니다."""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """전화번호 조회 명령어 - 모든 매칭 결과 표시"""
    user = update.effective_user
    
    # 비밀번호 인증 확인
    if user.id not in authenticated_users:
        await update.message.reply_text(
            "⛔ **허용된 사용자가 아닙니다.**\n\n"
            "🔐 **비밀번호를 입력하세요.**\n\n"
            "📞 관리자에게 문의하세요."
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
    
    # 비밀번호 인증 확인
    if user.id not in authenticated_users:
        await update.message.reply_text(
            "⛔ **허용된 사용자가 아닙니다.**\n\n"
            "🔐 **비밀번호를 입력하세요.**\n\n"
            "📞 관리자에게 문의하세요."
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
    
    # 비밀번호 확인
    if message_text == ACCESS_PASSWORD:
        # 비밀번호 맞음 - 인증 완료
        authenticated_users.add(user.id)
        
        # 입력 메시지 즉시 삭제 (보안)
        try:
            await update.message.delete()
        except:
            pass
        
        success_text = f"""🎉 **인증 성공!** 

환영합니다, {user.first_name}님!

🔍 **TeleDB - 전화번호 조회 시스템**
📱 **사용 방법:**
• `01012345678` - 전화번호 바로 입력하여 조회
• `/help` - 상세 도움말 
• `/stats` - 데이터베이스 통계

💡 **간편 조회**: 전화번호만 입력하면 바로 검색 시작!

🔒 인증 완료! 이제 모든 기능을 사용할 수 있습니다."""
        await update.message.reply_text(success_text, parse_mode='Markdown')
        return
    
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
        # 비밀번호 인증 확인
        if user.id not in authenticated_users:
            await update.message.reply_text(
                "⛔ **허용된 사용자가 아닙니다.**\n\n"
                "📞 관리자에게 문의하세요."
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
                # datetime 객체를 문자열로 변환
                created_at = result['created_at']
                if hasattr(created_at, 'strftime'):
                    # datetime 객체인 경우
                    created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # 이미 문자열인 경우
                    created_str = str(created_at)[:19]
                response += f"   📅 등록일: {created_str}\n\n"
            
            response += "🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*"
            
            sent_msg = await update.message.reply_text(response, parse_mode='Markdown')
            # 응답 메시지와 사용자 입력 메시지 정확히 동시 삭제
            import asyncio
            asyncio.create_task(delete_both_messages_together(sent_msg, update.message, 30))
        else:
            formatted_phone = format_phone_number(cleaned_phone)
            sent_msg = await update.message.reply_text(f"❌ 전화번호 `{formatted_phone}`에 대한 정보를 찾을 수 없습니다.\n\n🗑️ *이 메시지는 30초 후 자동 삭제됩니다.*", parse_mode='Markdown')
            # 응답 메시지와 사용자 입력 메시지 정확히 동시 삭제
            import asyncio
            asyncio.create_task(delete_both_messages_together(sent_msg, update.message, 30))
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

async def delete_both_messages_together(response_msg, user_msg, delay_seconds):
    """두 메시지를 정확히 동시에 삭제"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    
    # 두 메시지를 거의 동시에 삭제 (순차적이지만 매우 빠르게)
    try:
        await response_msg.delete()
    except:
        pass
    
    try:
        await user_msg.delete()
    except:
        pass

async def delete_messages_simultaneously(messages, delay_seconds):
    """여러 메시지를 정확히 동시에 삭제"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    
    # 모든 메시지를 동시에 삭제
    delete_tasks = []
    for message in messages:
        delete_tasks.append(asyncio.create_task(safe_delete_message(message)))
    
    # 모든 삭제 작업을 동시에 실행
    await asyncio.gather(*delete_tasks, return_exceptions=True)

async def safe_delete_message(message):
    """안전한 메시지 삭제"""
    try:
        await message.delete()
    except Exception:
        pass  # 삭제 실패해도 에러 무시

async def init_sample_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """샘플 데이터 초기화 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    if user.id != int(ADMIN_USER_ID):
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    await update.message.reply_text("🔄 샘플 데이터 초기화 중...")
    
    try:
        # 샘플 데이터 5개 추가
        sample_numbers = [
            ("01092999998", "김철수 - 삼성전자 개발팀"),
            ("01012345678", "이영희 - LG전자 마케팅부"),  
            ("01087654321", "박민수 - 현대자동차 디자인센터"),
            ("01055556666", "최지연 - 네이버 AI연구소"),
            ("01099998888", "김대한 - 카카오 서비스개발팀"),
        ]
        
        added_count = 0
        for phone, content in sample_numbers:
            success = add_phone_data(phone, content)
            if success:
                added_count += 1
        
        await update.message.reply_text(
            f"✅ **샘플 데이터 초기화 완료**\n\n"
            f"📊 추가된 레코드: {added_count}개\n\n"
            f"🧪 **테스트용 전화번호:**\n"
            f"• `01092999998` - 김철수 (삼성전자)\n"
            f"• `01012345678` - 이영희 (LG전자)\n"  
            f"• `01087654321` - 박민수 (현대자동차)\n"
            f"• `01055556666` - 최지연 (네이버)\n"
            f"• `01099998888` - 김대한 (카카오)\n\n"
            f"💡 위 번호들로 조회 테스트를 해보세요!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"샘플 데이터 초기화 오류: {e}")
        await update.message.reply_text(f"❌ 샘플 데이터 초기화 실패: {e}")

async def manual_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """수동 데이터 추가 (슈퍼어드민 전용)"""
    user = update.effective_user
    
    if user.id != int(ADMIN_USER_ID):
        await update.message.reply_text("❓ 알 수 없는 명령어입니다.")
        return
    
    # 사용법 체크
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "📝 **수동 데이터 추가**\n\n"
            "사용법: `/manual_add 전화번호 내용`\n\n"
            "예시:\n"
            "`/manual_add 01092999998 김철수-삼성전자`\n"
            "`/manual_add 01012345678 이영희-LG전자`",
            parse_mode='Markdown'
        )
        return
    
    phone_number = context.args[0]
    content = ' '.join(context.args[1:])
    
    try:
        # 전화번호 정리
        cleaned_phone = clean_phone_number(phone_number)
        if not validate_phone_number(cleaned_phone):
            await update.message.reply_text(f"❌ 올바르지 않은 전화번호: {phone_number}")
            return
        
        await update.message.reply_text(f"🔄 데이터 추가 중: {cleaned_phone}")
        
        # 데이터베이스에 추가
        success = add_phone_data(cleaned_phone, content)
        
        if success:
            # 추가 확인
            verify_results = search_phone(cleaned_phone)
            formatted_phone = format_phone_number(cleaned_phone)
            
            await update.message.reply_text(
                f"✅ **데이터 추가 성공**\n\n"
                f"📱 전화번호: `{formatted_phone}`\n"
                f"📝 내용: {content}\n"
                f"🔍 확인: {len(verify_results)}개 레코드 존재\n\n"
                f"💡 `{formatted_phone}` 로 조회 테스트 해보세요!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ **데이터 추가 실패**\n\n"
                f"데이터베이스 연결 문제일 수 있습니다.\n"
                f"Render 로그를 확인해주세요."
            )
        
    except Exception as e:
        logger.error(f"수동 데이터 추가 오류: {e}")
        await update.message.reply_text(f"❌ 데이터 추가 중 오류 발생: {e}")

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
    application.add_handler(CommandHandler("sa", sa_command))  # /sa로 간단하게
    application.add_handler(CommandHandler("비번변경", changepass_command))  # 비밀번호 변경
    
    # 사용자 승인 관련 핸들러 (dis7414 전용) - 영어 명령어만 사용
    application.add_handler(CommandHandler("approve", approve_user_command))
    application.add_handler(CommandHandler("disapprove", disapprove_user_command))
    application.add_handler(CommandHandler("users", list_users_command))
    
    # 관리자 권한 관련 핸들러 (dis7414 전용)
    application.add_handler(CommandHandler("admin", admin_user_command))
    application.add_handler(CommandHandler("unadmin", unadmin_user_command))
    application.add_handler(CommandHandler("admins", list_admins_command))
    application.add_handler(CommandHandler("init_sample", init_sample_data_command))
    application.add_handler(CommandHandler("manual_add", manual_add_command))
    
    # 일반 메시지 핸들러
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("모든 핸들러가 설정되었습니다.")