# tools/nexttrace.py

import subprocess
import env
import asyncio
from .utils import escape_markdown_v2  # 使用相对导入从同一目录下的 utils 模块导入
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

def execute_nexttrace(target, ipv6=False):
    """执行nexttrace命令并返回输出结果"""
    try:
        result = subprocess.run(
            ["nexttrace", "-M", "-r", "-C", target],
            capture_output=True, text=True)
        if result.returncode == 0:
            return escape_markdown_v2(result.stdout)
        else:
            return f"{env.MEOW_NAME}说，nexttrace命令执行失败了喵～"
    except Exception as e:
        return f"{env.MEOW_NAME}遇到了问题喵：{escape_markdown_v2(str(e))}"

async def nexttrace_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    args = context.args
    if chat_type == "private" and user_id in env.ALLOWED_USER_IDS:
        if args:
            target = args[0]
            # 发送初始的“请等待”消息
            message = await update.message.reply_text(f"`{env.MEOW_NAME}正在努力执行，请稍等喵～`", parse_mode=ParseMode.MARKDOWN_V2)
            loop = asyncio.get_running_loop()
            # 在后台线程中执行同步的execute_nexttrace函数
            output = await loop.run_in_executor(None, execute_nexttrace, target)
            # 更新消息
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, 
                                                 message_id=message.message_id, 
                                                 text=f"```\n{output}\n```", 
                                                 parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text(f"`{env.MEOW_NAME}提醒您，请指定目标IP喵～`", parse_mode=ParseMode.MARKDOWN_V2)
    else:
         await update.message.reply_text(f"`{env.MEOW_NAME}不理解你在说什么喵～?`", parse_mode=ParseMode.MARKDOWN_V2)
