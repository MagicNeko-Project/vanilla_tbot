import aiohttp
import env
from pydub import AudioSegment
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from openai import OpenAI
# 加载 openai 组件
# 谢谢 Cato 提示，写一行为正确写法
client = OpenAI(api_key=env.OPENAI_API_KEY2,base_url=env.OPENAI_API_BASE2)

# 初始化 Whisper 模型
# 在使用本地模型时可取消注释
#model = whisper.load_model(env.whisper_model)  # 选择适合的模型，例如"base"

# 下载进程，调用 aiohttp
async def download_file(file_url, file_name):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open(file_name, 'wb') as f:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)

async def transcribe_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_message = update.message.reply_to_message
    if not reply_message.voice:
        await update.message.reply_text("请回复一条语音消息。")
        return

    chat_id = update.effective_chat.id
    # 提示用户
    processing_message = await context.bot.send_message(chat_id=chat_id, text="处理中，请稍候...")

    # 获取语音文件的URL
    voice_file = await context.bot.get_file(reply_message.voice.file_id)
    voice_file_path = voice_file.file_path

    # 异步下载文件
    temp_ogg_path = "temp_voice.ogg"
    await download_file(voice_file_path, temp_ogg_path)

    # 转换格式 ogg -> wav
    audio_segment = AudioSegment.from_ogg(temp_ogg_path)
    # 在使用在线模型时可取消注释
    temp_mp3_path = "temp_vioce_converted.mp3"
    audio_segment.export(temp_mp3_path, format="mp3")
    # 在使用本地模型时可取消注释
    #temp_wav_path = "temp_voice_converted.wav"
    #audio_segment.export(temp_wav_path, format="wav")

    # 使用 Whisper 进行语音识别
    # 在使用本地模型时可取消注释
    #result = model.transcribe(temp_wav_path)
    #transcription = result['text']
    
    # 在使用在线模型时可取消注释
    audio_file= open(temp_mp3_path, "rb")
    transcript = client.audio.transcriptions.create(
        file=audio_file,
        model="whisper-1",
        response_format="text"
    )
    # 发送识别结果
    # 在使用本地模型时可取消注释
    #await processing_message.edit_text(f"识别结果：{transcription}")
    # 在使用在线模型时可取消注释
    await processing_message.edit_text(f"识别结果：{transcript}")

async def ai_speech_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip().lower()
    if update.message.reply_to_message and message_text == "!ai_speech":
        await transcribe_voice(update, context)
