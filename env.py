# env.py

import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TTS_API_PATH = os.getenv("TTS_API_PATH")
TTS_API_LANGUAGE = os.getenv("TTS_API_LANGUAGE", "auto")
TTS_API_TOPK = os.getenv("TTS_API_TOPK","20")
TTS_API_TOPP = os.getenv("TTS_API_TOPP", "0.6")
TTS_API_temperature = os.getenv("TTS_API_temperature","0.6")
TTS_C_NAME = os.getenv("TTS_C_NAME","Liuying")
VERSION = "0.2.7"
ALLOWED_IDS = [int(i) for i in os.getenv("ALLOWED_IDS", "").split(",") if i]
ALLOWED_USER_IDS = [int(i) for i in os.getenv("ALLOWED_USER_IDS", "").split(",") if i]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY2 = os.getenv("OPENAI_API_KEY2")
OPENAI_PROMPT_ROLE = os.getenv("OPENAI_PROMPT_ROLE", "AI助手")
OPENAI_ENGINE = os.getenv("OPENAI_ENGINE", "gpt-3.5-turbo")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_BASE2 = os.getenv("OPENAI_API_BASE2", "https://api.openai.com/v1")
OPENAI_IMAGE_RESOLUTION = os.getenv("OPENAI_IMAGE_RESOLUTION", "1024x1024")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
OPENAI_IMAGE_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "standard")
MEOW_NAME = os.getenv("MEOW_NAME", "香草")
HITOKOTO_API_URL = os.getenv("HITOKOTO_API_URL", "https://v1.hitokoto.cn/")
NBNHHSH_API= os.getenv("NBNHHSH_API", "https://lab.magiconch.com/api/nbnhhsh/")
RSS_TIME_STR = os.getenv("RSS_TIME_STR", "1800")
RSS_DB_PATH = os.getenv("RSS_DB_PATH", "rss_sqlite.db")
whisper_model = os.getenv("whisper_model", "base")
CYANBOT_DATABASE_URL = os.getenv("CYANBOT_DATABASE_URL")
CYANBOT_DATABASE_NAME =os.getenv("CYANBOT_DATABASE_NAME")
CYANBOT_MESSAGE_COUNT = os.getenv("CYANBOT_MESSAGE_COUNT","60")
#GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#LIVE_DATABASE_PATH = os.getenv("LIVE_DATABASE_PATH","./live.db")
#YOUTUBE_API_SERVICE_NAME = os.getenv("YOUTUBE_API_SERVICE_NAME","youtube")
#YOUTUBE_API_VERSION = os.getenv("YOUTUBE_API_SERVICE_NAME","v3")
#LIVE_DIRECTORY = os.getenv("LIVE_DIRECTORY","./live_directory/") 
#JUHE_API_KEY = os.getenv("JUHE_API_KEY")