# tools/utils.py

def escape_markdown_v2(text):
    """转义MarkdownV2特殊字符"""
    escape_chars = '_*[]()~>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)