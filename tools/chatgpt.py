# tools/chatgpt.py
# 加载变量
import env
import asyncio
import logging
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ContextTypes,
    CallbackContext,
)
from openai import OpenAI

# 加载 openai 组件
client = OpenAI(api_key=env.OPENAI_API_KEY)
client = OpenAI(base_url=env.OPENAI_API_BASE)

# 用户ID映射到其对话历史
user_chat_histories = {}  

# 加载日志模块
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

# 实现对话能力，由 ChatGPT 提供
async def ai_chat(update: Update, context: CallbackContext) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MEOW_NAME}这里的小秘密喵。")
        return
    
    input_text = " ".join(context.args)
    if not input_text:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"喵～没有文字是要怎么聊天呢？给喵娘点东西说吧～")
        return
    
    # 向用户展现正在输入的状态
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    # 延时，以确保用户体验
    await asyncio.sleep(1)
    
    if user_id not in user_chat_histories:
        user_chat_histories[user_id] = []
    
    messages = user_chat_histories[user_id] + [{"role": "user", "content": input_text}]
    
    try:
        temp_message = await context.bot.send_message(chat_id=update.effective_chat.id, text=f"喵～{env.MEOW_NAME}正在思考怎么回复您...")
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
        logger.error(f"喵～在思考中遇到了一点小麻烦: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=temp_message.message_id,
            text="喵～出了点小状况，暂时回答不了您的问题，再试试或者联系管理员吧～"
        )

# 重置对话
async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MEOW_NAME}这里的小秘密喵。")
        return

    # 重置对话历史
    if user_id in user_chat_histories:
        user_chat_histories[user_id] = []
        await update.message.reply_text(f"{env.MEOW_NAME}的对话记忆已经清空了喵，让我们开始新的故事吧！")
    else:
        await update.message.reply_text(f"喵？似乎还没有与{env.MEOW_NAME}的旧对话喵～")
