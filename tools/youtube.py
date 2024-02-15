import sqlite3
import asyncio
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import os
import re
import env

# 白名单
def is_allowed(entity_id: int) -> bool:
    return entity_id in env.ALLOWED_IDS

async def download_video_with_progress(update, context, video_url, directory):
    cmd = f"yt-dlp {video_url} -o '{directory}/%(title)s.%(ext)s'"

    progress_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="下载开始...")

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    last_progress = None
    async for line in process.stdout:
        decoded_line = line.decode()  # 手动解码
        match = re.search(r"(\d{1,3}(?=%))", decoded_line)
        if match:
            progress = match.group()

            if progress != last_progress:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=progress_message.message_id,
                        text=f"下载进度: {progress}%"
                    )
                    last_progress = progress
                except Exception as e:
                    print(f"Error updating message: {e}")
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=progress_message.message_id,
        text="下载完成。"
    )

def check_live_status(live_id):
    youtube = build(env.YOUTUBE_API_SERVICE_NAME, env.YOUTUBE_API_VERSION, developerKey=env.GOOGLE_API_KEY)
    request = youtube.videos().list(part='snippet,liveStreamingDetails', id=live_id)
    response = request.execute()

    if response['items']:
        live_status = response['items'][0]['snippet']['liveBroadcastContent']
        if live_status == 'live':
            return True
    return False

async def download_video(video_url, directory):
    cmd = f"yt-dlp {video_url} -o '{directory}/%(title)s.%(ext)s'"
    process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    print(stdout.decode())

async def download_live_stream(live_id, directory):
    await download_video(f"https://www.youtube.com/watch?v={live_id}", directory)

async def yt_dlp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    if context.args:
        video_url = context.args[0]
        target_directory = env.LIVE_DIRECTORY
        await download_video_with_progress(update, context, video_url, target_directory)
    else:
        await update.message.reply_text('请提供视频URL。')

async def live_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    entity_id = update.effective_user.id if update.effective_chat.type == 'private' else update.effective_chat.id
    user_id = update.effective_user.id
    if not is_allowed(entity_id):
        await update.message.reply_text(f"喵～似乎您没有权限询问{env.MOEW_NAME}这里的小秘密喵。")
        return
    if context.args:
        live_id = context.args[0]
        target_directory = env.LIVE_DIRECTORY
        
        conn = sqlite3.connect(env.LIVE_DATABASE_PATH)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO live_monitor(user_id, live_id) VALUES (?, ?)", (user_id, live_id))
            conn.commit()
            await update.message.reply_text('已添加到监控列表。')
        except sqlite3.IntegrityError:
            await update.message.reply_text('已经在监控列表中。')
        finally:
            conn.close()
        
        await update.message.reply_text('直播监控已启动。')
    else:
        await update.message.reply_text('请提供直播ID。')
