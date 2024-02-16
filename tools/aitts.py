# tools/ai_tts.py
import env
import asyncio
import io
import urllib.parse
import traceback
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes,
    CallbackContext,
)
from aiohttp import ClientSession
# 用于音频处理
from pydub import AudioSegment
from dataclasses import dataclass
from .hitokoto import get_hitokoto
@dataclass
class TTSJob:
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    text: str
    language: str

# 创建一个队列（改异步？）
request_queue = asyncio.Queue(maxsize=65535)
shutdown_event = asyncio.Event()

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

async def ai_tts(update: Update, context: CallbackContext):
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限让{env.MEOW_NAME}发声喵。")
        return
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text(f"想要{env.MEOW_NAME}说点什么呢？给我点提示吧喵～")
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
        await update.message.reply_text(f"喵～似乎您没有权限让{env.MEOW_NAME}发声喵。")
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
            await update.message.reply_text(f"想要{env.MEOW_NAME}说点什么呢？给我点提示吧喵～")
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
                async with session.get(api_url, timeout=60) as response:
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