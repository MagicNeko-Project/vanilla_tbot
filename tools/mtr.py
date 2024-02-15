# tools/mtr.py

import subprocess
import env
from .utils import escape_markdown_v2  # 使用相对导入从同一目录下的 utils 模块导入
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

def execute_mtr(target, ipv6=False):
    """执行mtr命令并返回输出结果"""
    try:
        protocol_option = "-6" if ipv6 else "-4"
        result = subprocess.run(
            ["mtr", protocol_option, "-r", "-c", "1", "-n", target],
            capture_output=True, text=True)
        if result.returncode == 0:
            return escape_markdown_v2(result.stdout)
        else:
            return "MTR命令执行失败。"
    except Exception as e:
        return f"MTR命令执行出错: {escape_markdown_v2(str(e))}"
    
# mtr命令处理函数
async def mtr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    args = context.args
    if chat_type == "private" and user_id in env.ALLOWED_USER_IDS:
        if args:
            target = args[0]
            output = await execute_mtr(target)
            await update.message.reply_text(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("`请指定目标IP或域名。`", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(f"`喵～?`", parse_mode=ParseMode.MARKDOWN_V2)

# 应用类似修改于mtr4_command和mtr6_command函数
async def mtr4_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 此函数逻辑和mtr_command相同，因为mtr默认就是IPv4
    await mtr_command(update, context)

async def mtr6_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    args = context.args
    if chat_type == "private" and user_id in env.ALLOWED_USER_IDS:
        if args:
            target = args[0]
            output = await execute_mtr(target, ipv6=True)
            await update.message.reply_text(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN_V2)
        else:
            await update.message.reply_text("`请指定目标IP或域名。`", parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(f"`喵????要私聊哦~`", parse_mode=ParseMode.MARKDOWN_V2)
