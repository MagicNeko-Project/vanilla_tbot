import os
import logging
import asyncio
import psutil
import pynvml
import platform
import distro
import subprocess
from dotenv import load_dotenv
import openai
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
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
import json
import urllib.parse
import traceback

# 文件分离(帮助文本部分)
from help import help_command
# mtr 和 markdown_v2 过滤
from tools.mtr import execute_mtr
from tools.mtr import mtr_command
from tools.mtr import mtr4_command
from tools.mtr import mtr6_command
from tools.utils import escape_markdown_v2

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

# 一言
async def get_hitokoto():
    async with ClientSession() as session:
        try:
            response = await session.get(url=env.HITOKOTO_API_URL)
            if response.status == 200:
                data = await response.json()
                return data.get("hitokoto", "喵～貌似获取一言时出了点问题。")
        except Exception as e:
            logger.error(f"获取一言时发生错误：{e}")
            return "喵～获取一言时遇到了一点小困难。"

async def hitokoto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """向用户发送一条来自一言（Hitokoto）的句子。"""
    hitokoto = await get_hitokoto()
    await update.message.reply_text(hitokoto)

# ip查询
async def get_ip_info(ip_address: str) -> str:
    try:
        cmd = ['curl', f'https://api.live.bilibili.com/ip_service/v1/ip_service/get_ip_addr?ip={ip_address}']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.returncode == 0 and result.stdout:
            # 确保这里已经定义了 data
            data = json.loads(result.stdout)
            if data['code'] == 0:
                ip_info = data.get("data", {})
                response_text = (
                    f"*IP*: `{escape_markdown_v2(ip_info.get('addr', '未知'))}`\n"
                    f"*国家*: `{escape_markdown_v2(ip_info.get('country', '未知'))}`\n"
                    f"*省份*: `{escape_markdown_v2(ip_info.get('province', '未知'))}`\n"
                    f"*城市*: `{escape_markdown_v2(ip_info.get('city', '未知'))}`\n"
                    f"*ISP*: `{escape_markdown_v2(ip_info.get('isp', '未知'))}`\n"
                    f"*纬度*: `{escape_markdown_v2(ip_info.get('latitude', '未知'))}`\n"
                    f"*经度*: `{escape_markdown_v2(ip_info.get('longitude', '未知'))}`"
                )
                return response_text
            else:
                return "喵～获取IP地址的情报失败了呢。"
        else:
            return "喵～无法获得任何IP地址的秘密呢。"
    except subprocess.CalledProcessError as e:
        # Logger should be defined elsewhere in your code
        # logger.error(f"执行curl获取IP地址信息时发生错误：{e}")
        return "喵～在试图获取IP地址的秘密时我遇到了一点问题，请稍后再试吧。"
    except json.JSONDecodeError as e:
        # logger.error(f"解析IP信息时发生错误：{e}")
        return "喵～我在尝试解读收到的秘密信件时似乎出了点小错，文字好复杂的样子。"

# 确保这个函数定义在 get_ip_info 函数之外
def escape_markdown_v2(text: str) -> str:
    escape_chars = '_*[]()~>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def ip_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if args and len(args) == 1:
        ip_address = args[0]
        message = await get_ip_info(ip_address)
        # 发送Markdown格式的消息
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(1)  # 模拟正在处理的延时
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("请提供一个IP地址喵。例如：`/ipinfo 8.8.8.8`", parse_mode=ParseMode.MARKDOWN_V2)


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

# 查看用户和群组ID的命令
async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    # 根据聊天类型构建回复消息
    if update.effective_chat.type == "private":
        reply_message = f"您的用户ID是: {user_id}"
    else:
        reply_message = f"群组/频道ID是: {chat_id}\n您的用户ID是: {user_id}"
    
    await update.message.reply_text(reply_message)

async def system_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    """显示系统CPU、内存以及NVIDIA GPU占用信息（如果有的话）"""
    # 获取CPU信息
    cpu_name = platform.processor() or "未知CPU型号"
    cpu_usage = psutil.cpu_percent()

    # 获取内存信息
    memory = psutil.virtual_memory()
    memory_usage = memory.percent

    # 获取平台信息
    platform_name = platform.system()
    if platform_name == "Linux":
        if distro:
            platform_details = f"{distro.name()} {distro.version()} ({distro.codename()})"
        else:
            platform_details = "Linux (详细版本信息未知)"
    elif platform_name == "Windows":
        platform_details = f"Windows {platform.version()}"
    else:
        platform_details = f"{platform_name} {platform.release()}"
    
    # 格式化消息为Markdown
    message = (
        f"*平台*: `{platform_name}`\n"
        f"*CPU型号*: `{cpu_name}`\n"
        f"*CPU占用率*: `{cpu_usage}%`\n"
        f"*内存占用率*: `{memory_usage}%`\n"
    )

    # 尝试初始化NVML来访问NVIDIA GPU信息
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        for i in range(gpu_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            gpu_name = pynvml.nvmlDeviceGetName(handle)  # 确保名称以适当的字符集解码
            gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            message += (
                f"*NVIDIA GPU {i} ({gpu_name})*: GPU占用率: `{gpu_util.gpu}%`, 内存占用率: `{gpu_util.memory}%`\n"
            )
    except pynvml.NVMLError as e:
        message += "*NVIDIA GPU信息*: `不可用`\n"
    finally:
        try:
            pynvml.nvmlShutdown()  # 关闭NVML
        except:
            pass  # 如果pynvml未初始化，则忽略错误

    # 发送Markdown格式的消息
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.MARKDOWN)

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

# 转义MarkdownV2特殊字符
def escape_markdown_v2(text):
    """转义MarkdownV2特殊字符"""
    escape_chars = '_*[]()~>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

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
