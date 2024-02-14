import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from aiohttp import ClientSession
from dataclasses import dataclass
import traceback

# 加载环境变量
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_PATH = os.getenv("API_PATH")
LANGUAGE = os.getenv("LANGUAGE")

# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# 测试用命令 hello, start
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Hello {update.effective_user.first_name}",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("欢迎使用 AI TTS 机器人，请使用 /ai_tts 命令开始。")


# 创建一个队列（改异步？）
request_queue = asyncio.Queue(maxsize=65535)
shutdown_event = asyncio.Event()
# print(request_queue.maxsize)


@dataclass
class TTSJob:
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    text: str
    language: str


# 定义命令处理函数
async def ai_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("请提供要转换的文本内容。")
        return

    # 将当前请求加入队列
    await update.message.reply_text("排队中，请稍候...")
    await request_queue.put(TTSJob(update, context, text, LANGUAGE))


async def ai_tts_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_to_message = update.message.reply_to_message
    if reply_to_message.from_user.id == context.bot.id:
        text = update.message.text
        await update.message.reply_text("排队中，请稍候...")
        await request_queue.put(TTSJob(update, context, text, LANGUAGE))


async def start_tts_task(context: ContextTypes.DEFAULT_TYPE):
    async with ClientSession() as session:
        while not shutdown_event.is_set() or not request_queue.empty():
            # 从队列中获取任务（设置超时1秒）
            try:
                job = await asyncio.wait_for(request_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue

            update = job.update
            request = {"text": job.text, "text_language": job.language}  # 指定变量

            try:
                async with session.post(API_PATH, json=request, timeout=10) as response:
                    if response.ok:
                        # 将音频数据发送回用户
                        content = await response.read()
                        await update.message.reply_voice(voice=content)
                    else:
                        # 失败时，解析错误信息并回复
                        error_info = await response.read()
                        await update.message.reply_text(
                            f"生成错误（失败）: {response.status}: {error_info}"
                        )
            except asyncio.TimeoutError:
                await update.message.reply_text("生成错误: 请求超时")
            except Exception as e:
                await update.message.reply_text(f"生成错误（异常）: {str(e)}")
                traceback.print_exc()
            finally:
                request_queue.task_done()  # 完成任务


def main():
    # 创建 bot 应用实例
    application = (
        ApplicationBuilder().token(TELEGRAM_TOKEN).concurrent_updates(True).build()
    )

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("ai_tts", ai_tts))
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
