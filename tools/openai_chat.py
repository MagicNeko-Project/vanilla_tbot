# tools/openai_chat.py
# 加载变量
import env
import asyncio
import logging
import requests
from io import BytesIO
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes,
    CallbackContext,
)
from openai import OpenAI

# 加载环境变量、OpenAI客户端
# 谢谢 Cato 提示，写一行为正确写法
client = OpenAI(api_key=env.OPENAI_API_KEY, base_url=env.OPENAI_API_BASE)

# 用户ID映射到其对话历史
user_chat_histories = {}

# 日志设置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 检查用户是否在白名单中
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

# 实现对话功能
async def ai_chat(update: Update, context: CallbackContext) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text("喵~ 你没有权限使用这个功能喵！")
        return
    
    input_text = " ".join(context.args)
    if not input_text:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="喵～没有文字是要怎么聊天呢？给喵娘点东西说吧～")
        return
    
    # 显示正在输入的状态给用户
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)  # 模拟延时
    
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []
    
    messages = user_chat_histories[user_id] + [{"role": "user", "content": input_text}]
    
    try:
        temp_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="喵～正在思考怎么回复您...")
        response = client.chat.completions.create(model=env.OPENAI_ENGINE,
                                                  messages=messages,
                                                  max_tokens=150)
        output_text = response.choices[0].message.content.strip()

        user_chat_histories[user_id].append({"role": "user", "content": input_text})
        user_chat_histories[user_id].append({"role": "assistant", "content": output_text})
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=temp_message.message_id,
            text=output_text
        )
    except Exception as e:
        logger.error(f"遇到了一点小麻烦: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=temp_message.message_id,
            text="喵～出了点小状况，暂时回答不了您的问题，再试试或者联系管理员吧～"
        )

# 实现重置对话功能
async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("喵~ 你没有权限使用这个功能喵！")
        return
    
    if user_id in user_chat_histories:
        user_chat_histories[user_id] = []
        await update.message.reply_text(f"{env.MEOW_NAME}的对话记忆已经清空了喵，让我们开始新的故事吧！")
    else:
        await update.message.reply_text(f"喵？似乎还没有与{env.MEOW_NAME}的旧对话喵～")

# 实现图片生成功能
async def ai_generate_image(update: Update, context: CallbackContext) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    if not is_allowed(entity_id):
        await update.message.reply_text("喵~ 你没有权限使用这个功能喵！")
        return
    
    # 解析用户输入的参数，包括prompt、分辨率、模型和质量
    args = context.args
    prompt_text = args[0] if len(args) > 0 else ""
    resolution = args[1] if len(args) > 1 else env.OPENAI_IMAGE_RESOLUTION
    model = args[2] if len(args) > 2 else env.OPENAI_IMAGE_MODEL
    quality = args[3] if len(args) > 3 else env.OPENAI_IMAGE_QUALITY

    if not prompt_text:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="喵～需要一些描述来生成图片喵～")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    
    try:
        temp_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="喵～正在努力画画...")

        # 使用 OpenAI 图片生成接口生成图片
        response = client.images.generate(
            model=model,
            prompt=prompt_text,
            size=resolution,
            quality=quality,
            n=1
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image = BytesIO(image_response.content)
        
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
        
    except Exception as e:
        logger.error(f"生成图片时遇到了一点小麻烦: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=temp_message.message_id,
            text="喵～画画出了点小状况，暂时无法完成画作，再试试或者联系管理员吧～"
        )