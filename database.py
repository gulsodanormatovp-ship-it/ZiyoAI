import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect("ziyoai_pro.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # Foydalanuvchilar va balans, API kalitlar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 500,
            api_key TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    
    # Chatlar tarixi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            mode TEXT DEFAULT 'standard',
            created_at TEXT
        )
    """)
    
    # Xabarlar bazasi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            sender TEXT,
            content TEXT,
            timestamp TEXT
        )
    """)
    
    # Media galereyasi (Rasmlar va videolar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            file_url TEXT,
            media_type TEXT,
            created_at TEXT
        )
    """)
    
    # Marketplace agentlar/promptlar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketplace (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id TEXT,
            title TEXT,
            description TEXT,
            prompt_template TEXT,
            rating REAL DEFAULT 5.0
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")
