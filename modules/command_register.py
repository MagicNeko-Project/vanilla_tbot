# command_register.py

def register_commands(application, dynamic_import, CommandHandler):

    # 动态导入并注册命令处理器
    commands = [
        ("start", "tools.base", "start"),
        ("hello", "tools.base", "hello"),
        ("cato", "tools.egg", "cato"),
        ("cyan", "tools.egg", "cyan"),
        ("yitong", "tools.egg", "yitong"),
        ("ai_tts", "tools.aitts", "ai_tts"),
        ("ai_image", "tools.openai_chat", "ai_generate_image"), # 图片生成逻辑暂时禁用，太贵了
        ("ai_chat", "tools.openai_chat", "ai_chat"),
        ("ai_translate", "tools.openai_chat", "ai_translate"),
        ("ai_whisper","tools.aispeech","ai_speech_voice"),
        ("version", "tools.base", "version"),
        ("id", "tools.tginfo", "id_command"),
        ("help", "help", "help_command"),
        ("sys_stats", "tools.systeminfo", "system_stats"),
        ("mtr", "tools.mtr", "mtr_command"),
        ("mtr4", "tools.mtr", "mtr4_command"),
        ("mtr6", "tools.mtr", "mtr6_command"),
        ("reset_chat", "tools.openai_chat", "reset_chat"),
        ("hitokoto", "tools.hitokoto", "hitokoto_command"),
        ("hitokoto_tts", "tools.aitts", "hitokoto_tts"),
        ("ipinfo", "tools.ipinfo", "ip_info_command"),
        ("nbnhhsh_help", "tools.nbnhhsh", "nbnhhsh_help"),
        ("nbnhhsh_add", "tools.nbnhhsh", "nbnhhsh_add"),
        ("nbnhhsh", "tools.nbnhhsh", "nbnhhsh"),
        ("nexttrace", "tools.nexttrace", "nexttrace_command"),
        ("hxw", "tools.hxw", "hx_handler"),
        ("rss_subscribe", "tools.rss", "rss_subscribe"),
        ("url_clean", "tools.cleanurl", "clear_url_handler"),
    ]

    for command in commands:
        handler_function = dynamic_import(command[1], command[2])
        application.add_handler(CommandHandler(command[0], handler_function))