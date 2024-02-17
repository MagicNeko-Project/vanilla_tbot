from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from unalix import clear_url
import re
import logging

# 设置日志进行错误跟踪
logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO
)

# 定义用于识别 URL 的正则表达式
url_re = re.compile(
    r"(([hHtTpP]{4}[sS]?)://)?([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
)

async def clear_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理接收到的含 URL 的消息，并返回清理后的 URL。"""
    message_text = update.message.text
    to_send = set()
    for input_url in url_re.finditer(message_text):
        found = input_url.group()
        try:
            clean_url = clear_url(found)
            if found != clean_url:
                to_send.add(clean_url)
        except Exception as e:
            logging.error(f"{e} - URL: {found}")

    if to_send:
        to_send_text = "\n\n".join(i for i in to_send)
        await update.message.reply_text(f"🧹 清洁的 URL:\n{to_send_text}")
    else:
        await update.message.reply_text("没有发现需要清理的链接，或者消息中不包含任何链接。")

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理内联查询，返回清理后的 URL。"""
    query = update.inline_query.query
    results = []

    for input_url in url_re.finditer(query):
        clean_url_result = clear_url(input_url.group())
        results.append(
            InlineQueryResultArticle(
                id=clean_url_result,
                title="清洁后的 URL",
                input_message_content=InputTextMessageContent(clean_url_result)
            )
        )

    if not results:
        results = [InlineQueryResultArticle(
            id='placeholder',
            title="未发现 URL",
            input_message_content=InputTextMessageContent("没有发现需要清洁的 URL。")
        )]

    await update.inline_query.answer(results)

