from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from tools.hxw import to_hx
from tools.hxw import to_hx_hxjt
from tools.hxw import to_hx_hxft
from tools.nbnhhsh import nbnhhsh_guess
from tools.nbnhhsh import hash_text

from tools.openai_chat import client
from unalix import clear_url
import re
from uuid import uuid4
import logging
import env  # 确保导入 env 模块
import asyncio  # 导入 asyncio 用于实现延迟

# 日志设置
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# url 清理正则表达式
url_pattern = re.compile(
    r"(([hHtTpP]{4}[sS]?)://)?([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
)

# 存储最近一次查询时间的字典
user_last_query_time = {}

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query_text = update.inline_query.query
    user_id = update.effective_user.id

    # 如果没有输入，直接返回
    if not query_text:
        return

    # 更新最近一次查询时间
    current_time = asyncio.get_event_loop().time()
    user_last_query_time[user_id] = current_time

    # 等待3秒，检查是否有新的输入
    await asyncio.sleep(3)

    # 检查3秒后查询时间是否有变化
    if user_last_query_time[user_id] != current_time:
        return

    results = []

    # 处理 `ai_translate` 和 `fanyi` 功能
    if query_text.startswith('!ai_translate') or query_text.startswith('!fanyi'):
        user_id_str = str(user_id)  # 将 user_id 转换为字符串
        if user_id_str in env.AIFANYI_ALLOWED_IDS:
            include_original = query_text.startswith('!ai_translate_o') or query_text.startswith('!fanyi_o')
            
            # 检测使用的是哪个命令
            if query_text.startswith('!ai_translate '):
                input_text = query_text[len('!ai_translate '):].strip()
            elif query_text.startswith('!ai_translate_o '):
                input_text = query_text[len('!ai_translate_o '):].strip()
            elif query_text.startswith('!fanyi '):
                input_text = query_text[len('!fanyi '):].strip()
            elif query_text.startswith('!fanyi_o '):
                input_text = query_text[len('!fanyi_o '):].strip()
            else:
                input_text = query_text.strip()  # 处理没有命令前缀的情况

            translation_prompt = {
                "role": "system",
                "content": "你是一个好用的翻译助手。请将我的中文翻译成英文，将所有非中文的翻译成中文。我发给你所有的话都是需要翻译的内容，你只需要回答翻译结果。翻译结果请符合中文的语言习惯。"
            }

            messages = [translation_prompt, {"role": "user", "content": input_text}]

            try:
                response = client.chat.completions.create(
                    model=env.OPENAI_ENGINE,
                    messages=messages,
                    max_tokens=3000
                )
                translated_text = response.choices[0].message.content.strip()

                if include_original:
                    output_text = f"{translated_text}\n\n原始文本: {input_text}"
                else:
                    output_text = translated_text

                results.append(
                    InlineQueryResultArticle(
                        id="translate_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                        title='翻译结果',
                        description=translated_text,
                        input_message_content=InputTextMessageContent(output_text)
                    )
                )
            except Exception as e:
                logger.error(f"遇到了一点小麻烦: {e}")
                results.append(
                    InlineQueryResultArticle(
                        id="translate_error_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                        title='翻译出错',
                        description="喵～出了点小状况，暂时无法处理您的翻译请求。",
                        input_message_content=InputTextMessageContent("喵～出了点小状况，暂时无法处理您的翻译请求。")
                    )
                )
        else:
            results.append(
                InlineQueryResultArticle(
                    id="translate_not_allowed_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                    title='没有权限',
                    description="喵~ 你没有权限使用这个功能喵！",
                    input_message_content=InputTextMessageContent("喵~ 你没有权限使用这个功能喵！")
                )
            )

        # 提交结果并返回，避免执行其他命令分析
        await context.bot.answer_inline_query(update.inline_query.id, results)
        return

    # 处理 URL 清理
    for match in url_pattern.finditer(query_text):
        cleaned_url = clear_url(match.group())
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),  # ID 使用 uuid4 生成
                title="清洁后的 URL",
                description=cleaned_url,
                input_message内容=InputTextMessageContent(cleaned_url)
            )
        )

    # 如果 results 为空，即没有匹配的 URL，可以考虑添加占位符结果
    if not results:
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),  # 同样使用 uuid4 生成唯一 ID
            title="未发现 URL",
            description="没有发现需要清洁的 URL。",
            input_message内容=InputTextMessageContent("没有发现需要清洁的 URL。")
        ))

    # Nbnhhsh（猜测缩写）处理逻辑
    guessed_acronyms = await nbnhhsh_guess(query_text)
    if guessed_acronyms:
        result_id = await hash_text(guessed_acronyms)  # 确保这个异步函数有效且返回唯一标识
        acronym_parts = guessed_acronyms.split(': ')
        title = acronym_parts[0] if acronym_parts[0] else "能不能好好说话"
        description = acronym_parts[1] if len(acronym_parts) > 1 else "无描述"
        results.append(
            InlineQueryResultArticle(
                id="nb_" + result_id,  # 前缀确保 ID 唯一
                title=title,
                description=description,
                input_message内容=InputTextMessageContent(guessed_acronyms)
            )
        )

    # 转火星文处理逻辑
    hx_text = to_hx(query_text)
    if hx_text:
        results.append(
            InlineQueryResultArticle(
                id="hx_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='从简繁转火星文',
                description=hx_text,
                input_message内容=InputTextMessageContent(hx_text)
            )
        )
    # 火星文转简体处理逻辑
    hx_text_jt = to_hx_hxjt(query_text)
    if hx_text_jt:
        results.append(
            InlineQueryResultArticle(
                id="hx_jt_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='火星文转简体',
                description=hx_text_jt,
                input_message内容=InputTextMessageContent(hx_text_jt)
            )
        )
    # 火星文转繁体处理逻辑
    hx_text_ft = to_hx_hxft(query_text)
    if hx_text_ft:
        results.append(
            InlineQueryResultArticle(
                id="hx_ft_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='火星文转繁体',
                description=hx_text_ft,
                input_message内容=InputTextMessageContent(hx_text_ft)
            )
        )

    # 提交结果
    await context.bot.answer_inline_query(update.inline_query.id, results)
