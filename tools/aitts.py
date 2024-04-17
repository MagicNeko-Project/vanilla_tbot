# tools/ai_tts.py
# 本项目的原始功能

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
    # 将当前请求加入队列
    # 出于减少多余消息量的考量，此提示由聊天动作代替
    #await update.message.reply_text("排队中，请稍候...")
    await request_queue.put(TTSJob(update, context, text, env.TTS_API_LANGUAGE))

# 修改成 CallbackContext 用于聊天动作
async def ai_tts_text(update: Update, context: CallbackContext):
    # 检查 update.message 是否存在
    if update.message is None:
        # 如果 update.message 不存在，直接返回
        return
    
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限让{env.MEOW_NAME}发声喵。")
        return
    
    # 现在我们知道 update.message 存在，可以安全地检查 .text 属性
    command_text = update.message.text.strip() if update.message.text else ""
    if command_text.lower() == "!ai_tts":
        # 检查 reply_to_message 是否存在，并且 reply_to_message.text 也存在
        if update.message.reply_to_message and update.message.reply_to_message.text:
            text = update.message.reply_to_message.text
            await request_queue.put(TTSJob(update, context, text, env.TTS_API_LANGUAGE))
        else:
            await update.message.reply_text(f"想要{env.MEOW_NAME}说点什么呢？给我点提示吧喵～")

# pydub 处理，仍需要 ffmpeg
# 定义异步函数以启动TTS任务
async def start_tts_task(context: ContextTypes.DEFAULT_TYPE):
    # 创建异步会话
    async with ClientSession() as session:
        # 当未收到停止事件或请求队列不为空时持续进行
        while not shutdown_event.is_set() or not request_queue.empty():
            try:
                # 尝试从请求队列中获取任务，设置超时为1秒
                job = await asyncio.wait_for(request_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                # 如果等待超时，则继续下一个循环
                continue
                
            # 获取更新信息
            update = job.update

            # 将环境变量值转换为浮点数，确保API可以正确解析
            try:
                top_k = int(env.TTS_API_TOPK)  # 确保 top_k 是整数
                top_p = float(env.TTS_API_TOPP)
                temperature = float(env.TTS_API_temperature)
            except ValueError as e:
                await update.message.reply_text("环境变量配置错误: 无法将 top_k/top_p/temperature 转换为适当的类型")
                continue  # 转换失败时跳过此任务
            # 使用转换后的浮点数构造请求体
            body = {
                "cha_name": env.TTS_C_NAME,
                "text": urllib.parse.quote(job.text),
                "top_k": top_k,
                "top_p": top_p,
                "temperature": temperature,
            }

            # 设置请求头，声明内容类型为JSON
            headers = {"Content-Type": "application/json"}

            try:
                # 向用户发送聊天动作提示，表明正在录制语音
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
                # 发送POST请求到TTS API，附上JSON数据和头信息
                async with session.post(env.TTS_API_PATH, json=body, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        # 请求成功，读取响应内容
                        content = await response.read()
                        # 将响应内容转换为音频
                        audio = AudioSegment.from_file(io.BytesIO(content), format="wav")
                        buffer = io.BytesIO()
                        # 导出音频为OGG格式
                        audio.export(buffer, format="ogg", codec="libopus")
                        buffer.seek(0)
                        # 发送语音消息给用户
                        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=buffer)
                    else:
                        # 请求失败，获取错误信息反馈给用户
                        error_info = await response.text()
                        await update.message.reply_text(
                            f"生成错误（失败）: {response.status}: {error_info}"
                        )
            except asyncio.TimeoutError:
                # 处理请求超时异常
                await update.message.reply_text("生成错误: 请求超时")
            except Exception as e:
                # 处理其他异常，打印异常信息
                await update.message.reply_text(f"生成错误（异常）: {str(e)}")
                traceback.print_exc()
            finally:
                # 任务完成，标记队列任务已处理
                request_queue.task_done()

# 一言 x aitts
async def hitokoto_tts(update: Update, context: CallbackContext) -> None:
    """获取一言并通过TTS转换为语音消息发送。"""
    # 获取一言
    hitokoto = await get_hitokoto()
    # 将一言文本放入TTS队列处理
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_VOICE)
    await request_queue.put(TTSJob(update, context, hitokoto, env.TTS_API_LANGUAGE))