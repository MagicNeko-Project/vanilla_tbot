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

HELP_TEXT = '''能不能好好说话 Bot 使用说明

1. 私聊直接发送你不明白的缩写或包含缩写的文本
2. 群聊回复别人信息，加上 `/nbnhhsh` 
3. 群聊通过 `/nbnhhsh kimo` 查询 kimo

添加词条方法：

私聊或在群内发送： `/nbnhhsh_add kimo 恶心` 以添加词条

上游地址： https://github.com/itorr/nbnhhsh
机器人地址： https://github.com/imlonghao/nbnhhsh_bot 
'''

async def nbnhhsh_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT)

async def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

async def submit_tran(word, text):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{NBNHHSH_API_BASE}translation/{word}', json={'text': text}) as resp:
            return await resp.json()

async def guess(text):
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
        guessed_text = await guess(text_to_guess)
        await update.message.reply_text(guessed_text or "找不到相关信息")

async def inlinequery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []
    guesses = await guess(query)
    for guess in guesses.split('\n'):
        results.append(
            InlineQueryResultArticle(
                id=await hash_text(guess),
                title=guess,
                input_message_content=InputTextMessageContent(guess)
            )
        )

    await update.inline_query.answer(results)


