# tools/system-info.py

import psutil
import platform
import pynvml
import platform
import distro
import env
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

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
