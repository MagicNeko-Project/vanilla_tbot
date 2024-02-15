# tools/tginfo.py
import env
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

# 查看用户和群组ID的命令
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    # 根据聊天类型构建回复消息
    if update.effective_chat.type == "private":
        reply_message = f"您的用户ID是: {user_id}"
    else:
        reply_message = f"群组/频道ID是: {chat_id}\n您的用户ID是: {user_id}"
    
    await update.message.reply_text(reply_message)
