import logging
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
)
from aiohttp import ClientSession
from dataclasses import dataclass
import traceback
# 用于音频处理
from pydub import AudioSegment
import io
# 引用 json 处理 ip 查询

import urllib.parse
import traceback

# 文件分离(帮助文本部分)
from help import help_command
# mtr 和 markdown_v2 过滤
from tools.mtr import mtr_command
from tools.mtr import mtr4_command
from tools.mtr import mtr6_command
from tools.systeminfo import system_stats
from tools.tginfo import id_command
from tools.ipinfo import ip_info_command
from tools.hitokoto import get_hitokoto
from tools.hitokoto import hitokoto_command
# 加载环境变量
from dotenv import load_dotenv
load_dotenv()
import env

# 加载 openai 组件
client = OpenAI(api_key=env.OPENAI_API_KEY)
client = OpenAI(base_url=env.OPENAI_API_BASE)

# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

user_chat_histories = {}  # 用户ID映射到其对话历史

# 测试用命令 hello, start
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"喵～ Hello，{update.effective_user.first_name}！我是{env.MOEW_NAME}喵。",
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"喵呜，很高兴你和{env.MOEW_NAME}我见面啦～ 使用 /ai_tts 让我用流萤的声音给你带来温暖吧喵！")

async def cyan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Cyan is cute!/盐喵可爱！")

async def version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """发送机器人的当前版本号给用户"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{env.MOEW_NAME}当前版本是这样的喵：{env.VERSION}",
    )

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

# 实现对话能力，由 ChatGPT 提供
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    input_text = " ".join(context.args)
    if not input_text:
        await update.message.reply_text(f"喵～给我些许文字，让{env.MOEW_NAME}开始愉快的对话吧！")
        return
    # 初始化用户的对话历史（如果不存在）
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []

    # 将系统消息和用户消息添加到对话历史中
    messages = user_chat_histories[user_id] + [
        {"role": "user", "content": input_text},
    ]

    try:
        response = client.chat.completions.create(model=env.OPENAI_ENGINE,
            messages=messages,
            max_tokens=150,
        )
        output_text = response.choices[0].message.content.strip()
        
        # 更新对话历史
        user_chat_histories[user_id].append({"role": "user", "content": input_text})
        user_chat_histories[user_id].append({"role": "assistant", "content": output_text})
        # 添加正在编辑动作
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        # 稍作等待，以确保用户能看到状态（可选）
        await asyncio.sleep(1)
        await update.message.reply_text(output_text)
    except Exception as e:
        logger.error(f"在调用OpenAI API时遇到异常: {e}")
        await update.message.reply_text("抱歉，处理您的请求时发生了错误。")

async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return

    # 重置对话历史
    if user_id in user_chat_histories:
        user_chat_histories[user_id] = []
        await update.message.reply_text(f"{env.MOEW_NAME}的对话记忆已经清空了喵，让我们开始新的故事吧！")
    else:
        await update.message.reply_text(f"喵？似乎还没有与{env.MOEW_NAME}的旧对话喵～")

# 定义命令处理函数
# 修改成 CallbackContext 用于聊天动作
async def ai_tts(update: Update, context: CallbackContext):
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限让{env.MOEW_NAME}发声喵。")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(f"想要{env.MOEW_NAME}说点什么呢？给我点提示吧喵～")
        return

    # 在这里添加正在录制的聊天动作
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
    # 将当前请求加入队列
    # 出于减少多余消息量的考量，此提示由聊天动作代替
    #await update.message.reply_text("排队中，请稍候...")
    await request_queue.put(TTSJob(update, context, text, env.TTS_API_LANGUAGE))

# 修改成 CallbackContext 用于聊天动作
async def ai_tts_reply(update: Update, context: CallbackContext):
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限让{env.MOEW_NAME}发声喵。")
        return
    reply_to_message = update.message.reply_to_message
    command_text = update.message.text.strip()
    # 检查命令是否为!aitts
    if command_text.lower() == "!aitts":
        if reply_to_message and reply_to_message.text:
            text = reply_to_message.text
            # 在这里添加正在录制的聊天动作
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
            # 出于减少多余消息量的考量，此提示由聊天动作代替
            #await update.message.reply_text("排队中，请稍候...")
            await request_queue.put(TTSJob(update, context, text, env.TTS_API_LANGUAGE))
        else:
            await update.message.reply_text(f"想要{env.MOEW_NAME}说点什么呢？给我点提示吧喵～")
    else:
        # 如果不是!aitts命令，可以在这里处理其他逻辑或忽略
        pass

# pydub 处理，仍需要 ffmpeg
async def start_tts_task(context: ContextTypes.DEFAULT_TYPE):
    async with ClientSession() as session:
        while not shutdown_event.is_set() or not request_queue.empty():
            try:
                job = await asyncio.wait_for(request_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
                
            update = job.update

            params = {
                "id": "0",
                "lang": env.TTS_API_LANGUAGE,
                "preset": "default",
                "top_k": env.TTS_API_TOPK,
                "top_p": env.TTS_API_TOPP,
                "temperature": env.TTS_API_temperature,
                "text": job.text,
            }
            query_string = urllib.parse.urlencode(params)
            api_url = f"{env.TTS_API_PATH}/voice/gpt-sovits?{query_string}"

            try:
                async with session.get(api_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.read()
                        audio = AudioSegment.from_file(io.BytesIO(content), format="wav")
                        buffer = io.BytesIO()
                        audio.export(buffer, format="ogg", codec="libopus")
                        buffer.seek(0)
                        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=buffer)
                    else:
                        error_info = await response.text()
                        await update.message.reply_text(
                            f"生成错误（失败）: {response.status}: {error_info}"
                        )
            except asyncio.TimeoutError:
                await update.message.reply_text("生成错误: 请求超时")
            except Exception as e:
                await update.message.reply_text(f"生成错误（异常）: {str(e)}")
                traceback.print_exc()
            finally:
                request_queue.task_done()

# 一言 x aitts
async def hitokoto_tts(update: Update, context: CallbackContext) -> None:
    """获取一言并通过TTS转换为语音消息发送。"""
    # 获取一言
    hitokoto = await get_hitokoto()
    # 将一言文本放入TTS队列处理
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
    await request_queue.put(TTSJob(update, context, hitokoto, env.TTS_API_LANGUAGE))

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

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
