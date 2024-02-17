# tools/cnnews.py

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import requests
from datetime import datetime
import env

NEWS_CACHE = {
    'date': None,
    'data': None
}
# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def fetch_hot_news():
    """从API获取热搜新闻"""
    url = "http://apis.juhe.cn/fapigx/networkhot/query"
    params = {"key": env.JUHE_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['error_code'] == 0:
            return result['result']['list']
    return []

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0):
    """响应/news命令或分页回调，发送热搜新闻"""
    today = datetime.now().date()
    if NEWS_CACHE['date'] != today:
        news_data = fetch_hot_news()
        NEWS_CACHE['date'] = today
        NEWS_CACHE['data'] = news_data
    else:
        news_data = NEWS_CACHE['data']
    
    start = page * 5  # 每页显示5条新闻
    end = start + 5
    news_items = news_data[start:end]

    if not news_items:
        text = '目前没有获取到更多热搜新闻数据。'
        await update.message.reply_text(text)
        return

    message_texts = [
    f"*{item['title']}*\n[阅读全文]({item['url']})" for item in news_items if 'url' in item
    ]
    message_text = '\n\n'.join(message_texts)

    if message_text.strip():
        try:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(message_text, parse_mode='Markdown')
            else:
                await update.message.reply_text(message_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error updating or sending message: {e}")
    else:
    # 消息文本为空时的处理
        error_message = "没有找到当前的新闻数据。"
    if update.callback_query:
        await update.callback_query.answer()
        # 下面使用 edit_message_text 或者 answer 回复用户
        await update.callback_query.answer(error_message, show_alert=True)
    else:
        await update.message.reply_text(error_message)

    keyboard = []
    if page > 0:
        keyboard.append([InlineKeyboardButton("上一页", callback_data=f"prev_{page-1}")])
    if len(news_data) > end:
        keyboard.append([InlineKeyboardButton("下一页", callback_data=f"next_{page+1}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        # 如果是从回调查询触发，则编辑之前的消息
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理分页按钮的回调查询"""
    query = update.callback_query
    query_data = query.data
    _, direction, page = query_data.split("_")
    page = int(page)
    await news(update, context, page)

