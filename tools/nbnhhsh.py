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


