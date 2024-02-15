from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
# 加载变量
import env

# 文件分离
from tools.base import start
from tools.base import cyan 
from tools.base import hello
from tools.base import version
from help import help_command
from tools.mtr import mtr_command
from tools.mtr import mtr4_command
from tools.mtr import mtr6_command
from tools.systeminfo import system_stats
from tools.tginfo import id_command
from tools.ipinfo import ip_info_command
from tools.hitokoto import hitokoto_command
from tools.chatgpt import ai_chat
from tools.chatgpt import reset_chat
from tools.aitts import ai_tts
from tools.aitts import ai_tts_reply
from tools.aitts import start_tts_task
from tools.aitts import hitokoto_tts

def main():
    # 创建 bot 应用实例
    application = (
        ApplicationBuilder().token(env.TELEGRAM_TOKEN).concurrent_updates(True).build()
    )

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("cyan", cyan))
    application.add_handler(CommandHandler("ai_tts", ai_tts))
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
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_tts_reply))

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
    main()
