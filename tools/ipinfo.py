# tools/ipinfo.py
import asyncio
import subprocess
import json
from telegram import Update
from telegram.constants import ChatAction
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

# ip查询
async def get_ip_info(ip_address: str) -> str:
    try:
        cmd = ['curl', f'https://api.live.bilibili.com/ip_service/v1/ip_service/get_ip_addr?ip={ip_address}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode == 0 and result.stdout:
            # 确保这里已经定义了 data
            data = json.loads(result.stdout)
            if data['code'] == 0:
                ip_info = data.get("data", {})
                response_text = (
                    f"*IP*: `{escape_markdown_v2(ip_info.get('addr', '未知'))}`\n"
                    f"*国家*: `{escape_markdown_v2(ip_info.get('country', '未知'))}`\n"
                    f"*省份*: `{escape_markdown_v2(ip_info.get('province', '未知'))}`\n"
                    f"*城市*: `{escape_markdown_v2(ip_info.get('city', '未知'))}`\n"
                    f"*ISP*: `{escape_markdown_v2(ip_info.get('isp', '未知'))}`\n"
                    f"*纬度*: `{escape_markdown_v2(ip_info.get('latitude', '未知'))}`\n"
                    f"*经度*: `{escape_markdown_v2(ip_info.get('longitude', '未知'))}`"
                )
                return response_text
            else:
                return "喵～获取IP地址的情报失败了呢。"
        else:
            return "喵～无法获得任何IP地址的秘密呢。"
    except subprocess.CalledProcessError as e:
        # Logger should be defined elsewhere in your code
        # logger.error(f"执行curl获取IP地址信息时发生错误：{e}")
        return "喵～在试图获取IP地址的秘密时我遇到了一点问题，请稍后再试吧。"
    except json.JSONDecodeError as e:
        # logger.error(f"解析IP信息时发生错误：{e}")
        return "喵～我在尝试解读收到的秘密信件时似乎出了点小错，文字好复杂的样子。"

# 确保这个函数定义在 get_ip_info 函数之外
def escape_markdown_v2(text: str) -> str:
    escape_chars = '_*[]()~>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def ip_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if args and len(args) == 1:
        ip_address = args[0]
        message = await get_ip_info(ip_address)
        # 发送Markdown格式的消息
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(1)  # 模拟正在处理的延时
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("请提供一个IP地址喵。例如：`/ipinfo 8.8.8.8`", parse_mode=ParseMode.MARKDOWN_V2)
