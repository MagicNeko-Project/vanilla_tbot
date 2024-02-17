from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from .hxw import to_hx
from .hxw import to_hx_hxjt
from .hxw import to_hx_hxft
from .nbnhhsh import nbnhhsh_guess
from .nbnhhsh import hash_text
from unalix import clear_url
import re
from uuid import uuid4


url_re = re.compile(
    r"(([hHtTpP]{4}[sS]?)://)?([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"
)

async def combined_inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return
    
    results = []
    # 处理 URL 清理
    for input_url in url_re.finditer(query):
        clean_url_result = clear_url(input_url.group())
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),  # ID 使用 uuid4 生成
                title="清洁后的 URL",
                description=clean_url_result,
                input_message_content=InputTextMessageContent(clean_url_result)
            )
        )

    # 如果 results 为空，即没有匹配的 URL，可以考虑添加占位符结果
    if not results:
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),  # 同样使用 uuid4 生成唯一 ID
            title="未发现 URL",
            description="没有发现需要清洁的 URL。",
            input_message_content=InputTextMessageContent("没有发现需要清洁的 URL。")
            )
        )

    # Nbnhhsh（猜测缩写）处理逻辑
    guesses_str = await nbnhhsh_guess(query)
    if guesses_str:
        guesses_list = guesses_str.split('\n')
        for guess_result in guesses_list:
            if guess_result:
                result_id = await hash_text(guess_result)  # 确保这个异步函数有效且返回唯一标识
                parts = guess_result.split(': ')
                title = parts[0] if parts[0] else "能不能好好说话"
                description = parts[1] if len(parts) > 1 else "无描述"
                results.append(
                    InlineQueryResultArticle(
                        id="nb_" + result_id,  # 前缀确保 ID 唯一
                        title=title,
                        description=description,
                        input_message_content=InputTextMessageContent(guess_result)
                    )
                )

    # 转火星文处理逻辑
    hx_text = to_hx(query)
    if hx_text:
        results.append(
            InlineQueryResultArticle(
                id="hx_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='从简繁转火星文',
                description=hx_text,
                input_message_content=InputTextMessageContent(hx_text)
            )
        )
    # 火星文转简体处理逻辑
    hx_text = to_hx_hxjt(query)
    if hx_text:
        results.append(
            InlineQueryResultArticle(
                id="hx_jt_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='火星文转简体',
                description=hx_text,
                input_message_content=InputTextMessageContent(hx_text)
            )
        )
    # 火星文转繁体处理逻辑
    hx_text = to_hx_hxft(query)
    if hx_text:
        results.append(
            InlineQueryResultArticle(
                id="hx_ft_" + str(uuid4()),  # 使用 uuid4 生成唯一 ID
                title='火星文转繁体',
                description=hx_text,
                input_message_content=InputTextMessageContent(hx_text)
            )
        )

    # 提交结果
    await context.bot.answer_inline_query(update.inline_query.id, results)