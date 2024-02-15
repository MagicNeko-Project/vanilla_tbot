# env.py

import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TTS_API_PATH = os.getenv("TTS_API_PATH")
TTS_API_LANGUAGE = os.getenv("TTS_API_LANGUAGE", "auto")
TTS_API_TOPK = os.getenv("TTS_API_TOPK","20")
TTS_API_TOPP = os.getenv("TTS_API_TOPP", "0.6")
TTS_API_temperature = os.getenv("TTS_API_temperature","0.6")
VERSION = "0.2.7"
ALLOWED_IDS = [int(i) for i in os.getenv("ALLOWED_IDS", "").split(",") if i]
ALLOWED_USER_IDS = [int(i) for i in os.getenv("ALLOWED_USER_IDS", "").split(",") if i]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROMPT_ROLE = os.getenv("OPENAI_PROMPT_ROLE", "AI助手")
OPENAI_ENGINE = os.getenv("OPENAI_ENGINE", "gpt-3.5-turbo")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
MOEW_NAME = os.getenv("MOEW_NAME", "香草")
HITOKOTO_API_URL = os.getenv("HITOKOTO_API_URL", "https://v1.hitokoto.cn/")
