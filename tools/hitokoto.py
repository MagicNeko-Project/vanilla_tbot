# tools/hitokoto.py
import env
import logging
from aiohttp import ClientSession
from telegram import Update
from telegram.ext import (
    ContextTypes,
)

# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
# 一言
async def get_hitokoto():
    async with ClientSession() as session:
        try:
            response = await session.get(url=env.HITOKOTO_API_URL)
            if response.status == 200:
                data = await response.json()
                return data.get("hitokoto", "喵～貌似获取一言时出了点问题。")
        except Exception as e:
            logger.error(f"获取一言时发生错误：{e}")
            return "喵～获取一言时遇到了一点小困难。"

async def hitokoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """向用户发送一条来自一言（Hitokoto）的句子。"""
    hitokoto = await get_hitokoto()
    await update.message.reply_text(hitokoto)
