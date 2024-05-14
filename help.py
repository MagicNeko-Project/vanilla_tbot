# help.py
import env
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# 帮助
    help_text = f"""
喵～很高兴遇见你，亲爱的旅行者呐！✨ 
这里是由{env.MEOW_NAME}提供服务的机器人喵。以下是你可以跟我玩耍的命令列表喵～🐾

- <code>/start</code> - 开始和{env.MEOW_NAME}的奇妙之旅。
- <code>/hello</code> - 让{env.MEOW_NAME}给你最温暖的问候喵～
- <code>/version</code> - 告诉你，我们的友情等级现在是多少了哦！
- <code>/help</code> - 需要{env.MEOW_NAME}帮助的时候，随时召唤我喵。
- <code>/ai_tts</code> - 给我一段文字，让我用我的声音告诉你它是什么样子的喵！
- <code>/hitokoto</code> - 让我告诉你一个来自远方的小秘密喵～
- <code>/hitokoto_tts</code> - 我会从一言中获取一段话，然后以我的甜美声音读给你听喵🎶 
- <code>/sys_stats</code> - 告诉你这个服务器的小秘密，包括 CPU、内存和 GPU 都在忙些什么喵。
- <code>/mtr</code> - 跟我一起去探索到达某个目的地的神秘路径吧，需要告诉我目的地的IP或者域名喵。例如： <code>/mtr 8.8.8.8</code> 。
- <code>/id</code> - 告诉你，这个群组或者聊天的秘密编号，还有你的编号也会告诉你喵。
- <code>/chat</code> - 和{env.MEOW_NAME}开始旅程吧喵!
- <code>/reset_chat</code> - 忘掉以前的对话，和{env.MEOW_NAME}开始一段新的旅程吧喵！
- <code>/ipinfo</code> - 查水表喵！
- <code>/url_clean</code> - 清理具有跟踪的链接，不要跟踪我喵！！！！

- <code>!ai_whisper</code> - 在语音回复该命令可以帮你识别喵！！(OpenAI API)
- <code>!ai_tts</code> - 在聊天中回复该命令可以帮你生成语音喵！！(Local API)
- <code>!ai_translate</code> - 在聊天中回复该命令可以帮你翻译喵！！(OpenAI API)

还有 inline 类型指令可以使用喵！

呜呼～{env.MEOW_NAME}在这里等着与你的每一次对话喵！如果你有任何疑问，或者想和我聊点什么，记得随时召唤我哦！🌟
{env.MEOW_NAME}的代码在 https://github.com/MagicNeko-Project/vanilla_tbot 这里喵。
    """
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode=ParseMode.HTML)