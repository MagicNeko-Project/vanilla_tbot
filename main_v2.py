from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    InlineQueryHandler,
)

# 加载变量
import env
# 文件分离
from tools.base import start,hello,version
from inline import combined_inline_query_handler
from help import help_command
from tools.mtr import mtr_command,mtr4_command,mtr6_command
from tools.systeminfo import system_stats
from tools.tginfo import id_command
from tools.ipinfo import ip_info_command
from tools.hitokoto import hitokoto_command
from tools.openai_chat import ai_chat,reset_chat,ai_generate_image
from tools.aispeech import ai_speech_voice
from tools.aitts import ai_tts,ai_tts_text,start_tts_task,hitokoto_tts
from tools.nbnhhsh import nbnhhsh_add,nbnhhsh_help,nbnhhsh
from tools.nexttrace import nexttrace_command
from tools.cleanurl import clear_url_handler
from tools.hxw import hx_handler
from tools.rss import db_connect, rss_subscribe ,check_rss_updates,RSS_TIME
from tools.egg import cato,cyan,yitong 
def main():
    # 创建 bot 应用实例
    application = (
        ApplicationBuilder().token(env.TELEGRAM_TOKEN).concurrent_updates(True).build()
    )

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("cato", cato))
    application.add_handler(CommandHandler("cyan", cyan))
    application.add_handler(CommandHandler("yitong", yitong))
    application.add_handler(CommandHandler("ai_tts", ai_tts))
    # 图片生成逻辑暂时禁用，太贵了
    # application.add_handler(CommandHandler("ai_image", ai_generate_image))
    application.add_handler(CommandHandler("ai_chat", ai_chat))
    application.add_handler(CommandHandler("version", version))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sys_stats", system_stats))
    application.add_handler(CommandHandler("mtr", mtr_command))
    application.add_handler(CommandHandler("mtr4", mtr4_command))
    application.add_handler(CommandHandler("mtr6", mtr6_command))
    application.add_handler(CommandHandler("chat", ai_chat))
    application.add_handler(CommandHandler("reset_chat", reset_chat))
    application.add_handler(CommandHandler("hitokoto", hitokoto_command))
    application.add_handler(CommandHandler("hitokoto_tts", hitokoto_tts))
    application.add_handler(CommandHandler("ipinfo", ip_info_command))
    application.add_handler(CommandHandler("nbnhhsh_help", nbnhhsh_help))
    application.add_handler(CommandHandler("nbnhhsh_add", nbnhhsh_add))
    application.add_handler(CommandHandler("nbnhhsh", nbnhhsh))
    application.add_handler(CommandHandler('nexttrace',nexttrace_command ))
    application.add_handler(CommandHandler("hxw", hx_handler))
    application.add_handler(InlineQueryHandler(combined_inline_query_handler))
    application.add_handler(CommandHandler("rss_subscribe", rss_subscribe,))
    application.add_handler(CommandHandler("url_clean", clear_url_handler))
    application.job_queue.run_repeating(check_rss_updates, interval=RSS_TIME, first=10)
    # 在后面加上分组，可以让两个操作同时使用
    # 由 Cato 提供建议
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_speech_voice), group=0)
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_tts_text), group=1)
    
    queue = application.job_queue
    queue.run_once(start_tts_task, when=1)

    application.run_polling()

    # async with application.updater as updater:

    #     # 启动处理 TTS 任务的线程
    #     # await application.updater.start_polling()
    #     await updater.start_polling()
    #     await application.create_task(start_tts_task())
    #     # 开始轮询
    #     # application.run_polling()

if __name__ == "__main__":

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                      (id INTEGER PRIMARY KEY, chat_id INTEGER, feed_url TEXT)''')
    conn.commit()
    conn.close()

    main()
