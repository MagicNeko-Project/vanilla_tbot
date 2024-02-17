# tools/nbnhhsh.py
# 能不能好好说话 
# 使用 chatgpt 转化 https://github.com/imlonghao/nbnhhsh_bot 该项目到本项目中

import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
import aiohttp
import env
import hashlib

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

NBNHHSH_API_BASE = env.NBNHHSH_API

HELP_TEXT = f'''能不能好好说话 插件使用说明喵~

添加词条的方法喵：

喵~ 在私聊或者群里面发送： `/nbnhhsh_add kimo 恶心` 可以添加新的词条喵！
要查询 kimo 的话，就在私聊或者群里发送： `/nbnhhsh kimo` 喵~

{env.MEOW_NAME}告诉你好好说话插件的上游地址在这里喵： https://github.com/itorr/nbnhhsh
是基于这位{env.MEOW_NAME}的代码朋友哦，地址在这儿喵： https://github.com/imlonghao/nbnhhsh_bot 

和{env.MEOW_NAME}一起，记得喵，好好说话喵~'''

async def nbnhhsh_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)

async def hash_text(text):
    hash_object = hashlib.sha256(text.encode())
    return hash_object.hexdigest()[:10]

async def submit_tran(word, text):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{NBNHHSH_API_BASE}translation/{word}', json={'text': text}) as resp:
            return await resp.json()

async def nbnhhsh_guess(text):
    words = [word for word in text.split() if word.isalnum()]
    if not words:
        return ': 找不到相关信息'

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{NBNHHSH_API_BASE}guess", json={"text": ','.join(words)}) as resp:
            response_json = await resp.json()

    return_response = ''
    for word in response_json:
        if 'trans' in word:
            return_response += f"{word['name']}: {', '.join(word['trans'])}\n"
        elif 'inputting' in word:
            return_response += f"{word['name']}: (?) {', '.join(word['inputting'])}\n"
        else:
            return_response += f"{word['name']}: 找不到相关信息\n"
    return return_response.strip() if return_response else ': 找不到相关信息'

async def nbnhhsh_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in env.ALLOWED_IDS:
        await update.message.reply_text("喵~ 你没有权限使用这个功能喵！")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text('添加词语用法： `/nbnhhsh_add 缩写 中文`', parse_mode='Markdown')
        return
    await submit_tran(args[0], args[1])
    await update.message.reply_text('添加成功，管理员审核后可见')

async def nbnhhsh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    text_to_guess = ' '.join(args) if args else update.message.reply_to_message.text if update.message.reply_to_message else ''
    if text_to_guess:
        guessed_text = await nbnhhsh_guess(text_to_guess)
        await update.message.reply_text(guessed_text or "找不到相关信息")

async def nbnhhsh_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []
    guesses_str = await nbnhhsh_guess(query)
    if not guesses_str:  # 如果没有猜测结果，可以提供一个默认结果
        results.append(
            InlineQueryResultArticle(
                id="default",  # 确保这个 ID 是唯一的
                title="未找到结果",
                input_message_content=InputTextMessageContent("未能找到关于此查询的结果。")
            )
        )
    else:
        guesses_list = guesses_str.split('\n')
        for guess_result in guesses_list:
            if guess_result:
                result_id = await hash_text(guess_result)
                parts = guess_result.split(': ')
                title = parts[0] if parts[0] else "未知标题"
                description = parts[1] if len(parts) > 1 else "无描述"
                results.append(
                    InlineQueryResultArticle(
                        id=result_id,
                        title=title,
                        description=description,  # 提供一个简短描述
                        input_message_content=InputTextMessageContent(guess_result)
                    )
                )

    await update.inline_query.answer(results, cache_time=10, is_personal=True)
