# main.py

import importlib
import env  # 保留环境变量的静态导入
from modules import command_register, rss_db # 修改了导入语句以引用新的模块

def dynamic_import(module_name, function_name=None):
    if function_name is None:
        return importlib.import_module(module_name)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)

def main():
    # 创建 bot 应用实例
    ApplicationBuilder = dynamic_import("telegram.ext", "ApplicationBuilder")
    CommandHandler = dynamic_import("telegram.ext", "CommandHandler")
    MessageHandler = dynamic_import("telegram.ext", "MessageHandler")
    filters = dynamic_import("telegram.ext", "filters")
    InlineQueryHandler = dynamic_import("telegram.ext", "InlineQueryHandler")

    application = (
        ApplicationBuilder().token(env.TELEGRAM_TOKEN).concurrent_updates(True).build()
    )

    # 使用 command_register 模块注册命令
    command_register.register_commands(application, dynamic_import, CommandHandler)

    # 动态导入复合查询处理器
    combined_inline_query_handler = dynamic_import("inline", "combined_inline_query_handler")
    application.add_handler(InlineQueryHandler(combined_inline_query_handler))

    # 动态导入并处理定时任务
    check_rss_updates = dynamic_import("tools.rss", "check_rss_updates")
    RSS_TIME = dynamic_import("tools.rss", "RSS_TIME")
    application.job_queue.run_repeating(check_rss_updates, interval=RSS_TIME, first=10)

    # 动态导入并添加分组处理器
    ai_speech_voice = dynamic_import("tools.aispeech", "ai_speech_voice")
    ai_tts_text = dynamic_import("tools.aitts", "ai_tts_text")
    ai_translate = dynamic_import("tools.openai_chat", "ai_translate")

    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_speech_voice), group=0)
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_tts_text), group=1)
    application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, ai_translate), group=2)

    # 动态导入并启动TTS任务
    start_tts_task = dynamic_import("tools.aitts", "start_tts_task")
    application.job_queue.run_once(start_tts_task, when=1)

    application.run_polling()

if __name__ == "__main__":
    rss_db.setup_database(dynamic_import)  # 修改了这里的调用
    main()
