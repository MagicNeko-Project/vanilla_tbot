# tools/rss.py

from telegram import Update, ext
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import feedparser
from datetime import datetime
from datetime import timedelta
import sqlite3
import env 

# 使用 env 模块中定义的变量
TOKEN = env.TELEGRAM_TOKEN
RSS_TIME = int(env.RSS_TIME_STR)
interval = timedelta(seconds=RSS_TIME)
DB_PATH = env.RSS_DB_PATH


# 数据库连接
def db_connect():
    return sqlite3.connect(DB_PATH)

# 订阅命令
async def rss_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    # 权限控制(ALLOWED_IDS)
    user_id = update.effective_user.id
    if user_id not in env.ALLOWED_IDS:
        await update.message.reply_text("喵~ 你没有权限使用这个功能喵！")
        return
    try:
        feed_url = ' '.join(context.args)
        if not feed_url:
            await update.message.reply_text('Please provide a URL to subscribe.')
            return

        connection = db_connect()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO subscriptions (chat_id, feed_url) VALUES (?,?)", (chat_id, feed_url))
        connection.commit()
        connection.close()

        await update.message.reply_text(f'Subscribed to {feed_url}')
    except Exception as e:
        print(e)
        await update.message.reply_text('An error occurred.')

# 检查更新函数
def fetch_feed_updates(feed_url):
    updates = []
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        published = entry.get('published_parsed') or entry.get('updated_parsed')
        if published:
            entry_published = datetime(*published[:6])
            if (datetime.now() - entry_published).total_seconds() < RSS_TIME:
                updates.append((entry.title, entry.link))
    return updates

# 定时检查更新
async def check_rss_updates(context: ext.CallbackContext) -> None:
    connection = db_connect()
    cursor = connection.cursor()
    cursor.execute("SELECT chat_id, feed_url FROM subscriptions")
    subscriptions = cursor.fetchall()
    connection.close()
    
    for chat_id, feed_url in subscriptions:
        updates = fetch_feed_updates(feed_url)
        for title, link in updates:
            message_text = f"<a href='{link}'>{title}</a>"
            await context.bot.send_message(chat_id=chat_id, text=message_text, parse_mode=ParseMode.HTML)
