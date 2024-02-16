from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from .hxw import to_hx
from .hxw import to_hx_hxjt
from .hxw import to_hx_hxft
from .nbnhhsh import nbnhhsh_guess
from .nbnhhsh import hash_text

async def combined_inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []

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
                id="hx_" + query.upper(),  # 确保 ID 是唯一的
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
                id="hx_jt_" + query.upper(),  # 确保 ID 是唯一的
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
                id="hx_ft_" + query.upper(),  # 确保 ID 是唯一的
                title='火星文转繁体',
                description=hx_text,
                input_message_content=InputTextMessageContent(hx_text)
            )
        )

    # 如果没有任何结果，可以添加一个默认结果
    if not results:
        results.append(
            InlineQueryResultArticle(
                id="default",  
                title="未找到结果",
                input_message_content=InputTextMessageContent("未能找到关于此查询的结果。")
            )
        )

    # 提交结果
    await context.bot.answer_inline_query(update.inline_query.id, results)