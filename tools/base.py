# tools/base.py

import env
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

# 测试用命令 hello, start
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"喵～ Hello，{update.effective_user.first_name}！我是{env.MEOW_NAME}喵。",
    )
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"喵呜，很高兴你和{env.MEOW_NAME}我见面啦～ 使用 /ai_tts 让我用流萤的声音给你带来温暖吧喵！")

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送机器人的当前版本号给用户"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{env.MEOW_NAME}当前版本是这样的喵：{env.VERSION}",
    )
