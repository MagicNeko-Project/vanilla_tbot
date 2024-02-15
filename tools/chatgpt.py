# tools/chatgpt.py

import env
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes,
)
import asyncio
from openai import OpenAI
import logging

# 加载 openai 组件
client = OpenAI(api_key=env.OPENAI_API_KEY)
client = OpenAI(base_url=env.OPENAI_API_BASE)

user_chat_histories = {}  # 用户ID映射到其对话历史

# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS
# 实现对话能力，由 ChatGPT 提供

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    input_text = " ".join(context.args)
    if not input_text:
        await update.message.reply_text(f"喵～给我些许文字，让{env.MOEW_NAME}开始愉快的对话吧！")
        return
    # 初始化用户的对话历史（如果不存在）
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []

    # 将系统消息和用户消息添加到对话历史中
    messages = user_chat_histories[user_id] + [
        {"role": "user", "content": input_text},
    ]

    try:
        response = client.chat.completions.create(model=env.OPENAI_ENGINE,
            messages=messages,
            max_tokens=150,
        )
        output_text = response.choices[0].message.content.strip()
        
        # 更新对话历史
        user_chat_histories[user_id].append({"role": "user", "content": input_text})
        user_chat_histories[user_id].append({"role": "assistant", "content": output_text})
        # 添加正在编辑动作
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        # 稍作等待，以确保用户能看到状态（可选）
        await asyncio.sleep(1)
        await update.message.reply_text(output_text)
    except Exception as e:
        logger.error(f"在调用OpenAI API时遇到异常: {e}")
        await update.message.reply_text("抱歉，处理您的请求时发生了错误。")

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return

    # 重置对话历史
    if user_id in user_chat_histories:
        user_chat_histories[user_id] = []
        await update.message.reply_text(f"{env.MOEW_NAME}的对话记忆已经清空了喵，让我们开始新的故事吧！")
    else:
        await update.message.reply_text(f"喵？似乎还没有与{env.MOEW_NAME}的旧对话喵～")
