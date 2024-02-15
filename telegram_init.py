import requests
import env

# 您的机器人Token，从BotFather获取
BOT_TOKEN = env.TELEGRAM_TOKEN

# 设置命令的API URL
url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"

# 定义命令列表
commands = [
    {"command": "hello", "description": "让机器人给你最温暖的问候。"},
    {"command": "version", "description": "查看友情等级。"},
    {"command": "help", "description": "获取帮助信息。"},
    {"command": "ai_tts", "description": "文字转语音服务。"},
    {"command": "hitokoto", "description": "获取一个小秘密。"},
    {"command": "hitokoto_tts", "description": "听一个小秘密。"},
    {"command": "sys_stats", "description": "查看服务器状态。"},
    {"command": "mtr", "description": "探索到达目的地的路径。"},
    {"command": "mtr4", "description": "探索IPv4路径。"},
    {"command": "mtr6", "description": "探索IPv6路径。"},
    {"command": "id", "description": "查看群组或用户ID。"},
    {"command": "chat", "description": "开始和机器人的对话。"},
    {"command": "reset_chat", "description": "重置对话历史。"},
    {"command": "ipinfo", "description": "查询IP信息。"},
]

# 按英文字母顺序对命令进行排序
commands.sort(key=lambda x: x["command"])

# 将“start”命令手动添加到列表的开始位置
commands.insert(0, {"command": "start", "description": "开始和机器人的奇妙之旅。"})

# 发起POST请求设置命令
response = requests.post(url, json={"commands": commands})

# 打印响应内容，查看是否成功
print(response.json())
