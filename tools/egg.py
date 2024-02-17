# tools/egg.py

from telegram import Update
from telegram.ext import (
    ContextTypes,
)

async def cyan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Cyan is cute!/盐喵可爱！")

async def cato(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Cato is delicious!/Cato 好吃！")

async def yitong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"桶是用来装东西的，看见了请呼叫我。")
