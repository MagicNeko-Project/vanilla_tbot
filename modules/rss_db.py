# rss_db.py

def setup_database(dynamic_import):
    # 这里使用 dynamic_import 来动态导入 db_connect
    db_connect = dynamic_import("tools.rss", "db_connect")
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                      (id INTEGER PRIMARY KEY, chat_id INTEGER, feed_url TEXT)''')
    conn.commit()
    conn.close()
