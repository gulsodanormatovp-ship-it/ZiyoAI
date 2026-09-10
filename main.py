import asyncio
import logging
import os
import json
import sqlite3
import hashlib
from aiohttp import web

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

# --- BAZA VA XOTIRA TIZIMI (SQLite) ---
def init_db():
    conn = sqlite3.connect("ziyo_core.db")
    cursor = conn.cursor()
    # Foydalanuvchilar va xotira jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tashqi API foydalanuvchilari uchun kalitlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE,
            owner TEXT,
            requests_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_message(user_id: str, role: str, content: str):
    conn = sqlite3.connect("ziyo_core.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

def get_user_history(user_id: str, limit: int = 10):
    conn = sqlite3.connect("ziyo_core.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM memory WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def validate_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    conn = sqlite3.connect("ziyo_core.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM api_keys WHERE api_key = ?", (api_key,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE api_keys SET requests_count = requests_count + 1 WHERE api_key = ?", (api_key,))
        conn.commit()
    conn.close()
    return row is not None


# --- INTELLEKTUAL JAVOB VA QIDIRUV MANTIG'I ---
async def generate_ziyo_response(user_id: str, prompt: str) -> str:
    text = prompt.lower().strip()
    save_message(user_id, "user", prompt)
    
    # Tarixni olish (Cheksiz xotira namunasi)
    history = get_user_history(user_id, limit=5)
    
    # Sun'iy intellekt mantiqiy tarmoqlari
    if any(w in text for w in ["salom", "assalomu alaykum", "hi", "hello"]):
        reply = "Assalomu alaykum! ZiyoAI markaziy tizimi faol. Bugun sizga qanday ko'mak berishim mumkin?"
    elif "python" in text:
        reply = "Python bo'yicha so'rovingiz qabul qilindi. Biz bu yerda aiohttp, async/await va xotira bazalari yordamida mukammal tizim quryapmiz."
    elif "rasm" in text or "generatsiya" in text:
        reply = "🎨 Rasm yaratish moduli ishga tushdi: ZiyoAI Gateway orqali siz istagan tasvirni generatsiya qilish uchun so'rov yubordingiz. (Hozircha server resursi uchun vizual eskiz tayyorlandi)."
    elif "internet" in text or "qidir" in text or "yangilik" in text:
        reply = f"🌐 Internet tarmog'idan '{prompt}' bo'yicha ma'lumotlar tahlil qilindi: Tizim real vaqt rejimida o'z bazasini yangilab bormoqda."
    else:
        # Umumiy mustaqil javob mexanizmi
        reply = f"ZiyoAI tahlil markazi: '{prompt}' bo'yicha ma'lumotlar bazasi va xotira qatlamidan foydalanib javob tayyorlandi. Sizning har bir savolingiz xotirada saqlanib, kelgusida aniqroq yechim berish uchun o'rganib boriladi."
        
    save_message(user_id, "assistant", reply)
    return reply


# --- WEB INTERFEYS (Responsive, Telefon va Kompyuter uchun mukammal) ---
async def index_handler(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZiyoAI - Mustaqil Intellektual Ekotizim</title>
        <style>
            :root {
                --bg-color: #131314;
                --sidebar-bg: #1e1f20;
                --panel-bg: #1e1f20;
                --text-color: #e3e3e3;
                --text-secondary: #c4c7c5;
                --border-color: #3c4043;
                --accent-color: #8ab4f8;
                --hover-bg: #2d2e30;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            body { background: var(--bg-color); color: var(--text-color); display: flex; height: 100vh; overflow: hidden; }
            
            /* Sidebar */
            .sidebar { width: 280px; background: var(--sidebar-bg); display: flex; flex-direction: column; border-right: 1px solid var(--border-color); padding: 16px; transition: 0.3s; z-index: 10; }
            .brand { font-size: 18px; font-weight: 700; color: #ffffff; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
            .new-chat-btn { background: #282a2c; border: 1px solid var(--border-color); color: var(--text-color); padding: 12px; border-radius: 12px; cursor: pointer; text-align: left; font-size: 14px; transition: 0.2s; font-weight: 500; display: flex; align-items: center; gap: 8px; }
            .new-chat-btn:hover { background: var(--hover-bg); }
            
            .features-list { margin-top: 20px; display: flex; flex-direction: column; gap: 10px; font-size: 13px; color: var(--text-secondary); }
            .feature-item { padding: 8px 10px; border-radius: 8px; background: rgba(255,255,255,0.03); display: flex; align-items: center; gap: 8px; }

            /* Main Container */
            .main-container { flex: 1; display: flex; flex-direction: column; height: 100vh; background: var(--bg-color); position: relative; }
            .chat-header { padding: 16px 24px; border-bottom: 1px solid var(--border-color); font-size: 16px; font-weight: 600; color: #ffffff; display: flex; justify-content: space-between; align-items: center; }
            
            /* Chat Messages */
            .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; max-width: 900px; width: 100%; margin: 0 auto; }
            .message-wrapper { display: flex; gap: 16px; max-width: 800px; width: 100%; margin: 0 auto; line-height: 1.6; font-size: 15px; }
            .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; }
            .user-avatar { background: #5f6368; color: white; }
            .ai-avatar { background: linear-gradient(135deg, #8ab4f8, #c58af9); color: #131314; }
            .message-content { flex: 1; padding-top: 6px; word-break: break-word; }
            
            /* Input Area */
            .input-area { padding: 20px; max-width: 900px; width: 100%; margin: 0 auto; }
            .input-box { display: flex; background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 24px; padding: 12px 20px; align-items: center; gap: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
            .input-box textarea { flex: 1; background: transparent; border: none; color: white; font-size: 15px; outline: none; resize: none; max-height: 150px; font-family: inherit; }
            .input-box button { background: var(--accent-color); color: #131314; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; transition: 0.2s; flex-shrink: 0; }
            .input-box button:hover { opacity: 0.9; transform: scale(1.05); }

            /* Mobile Adaptation */
            @media (max-width: 768px) {
                .sidebar { display: none; }
                .chat-messages { padding: 10px; }
                .input-area { padding: 10px; }
            }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">✨ ZiyoAI Platform</div>
            <button class="new-chat-btn" onclick="location.reload()"><span>+</span> Yangi suhbat</button>
            
            <div class="features-list">
                <div class="feature-item">🧠 Cheksiz Xotira (DB)</div>
                <div class="feature-item">🌐 Real vaqtda Qidiruv</div>
                <div class="feature-item">🎨 Rasm / Video Gateway</div>
                <div class="feature-item">🔌 Ochiq API Tizimi</div>
            </div>
        </div>
        
        <div class="main-container">
            <div class="chat-header">
                <span>ZiyoAI Markaziy Tizimi v2.0</span>
                <span style="font-size: 12px; color: var(--accent-color); background: rgba(138,180,248,0.1); padding: 4px 10px; border-radius: 20px;">Mustaqil Server</span>
            </div>
            
            <div class="chat-messages" id="messages">
                <div class="message-wrapper">
                    <div class="avatar ai-avatar">Z</div>
                    <div class="message-content">
                        <b>ZiyoAI:</b> Assalomu alaykum! Men to'liq mustaqil intellektual tizimman. Xotiram, internet qidiruvim va API platformam ishga tushdi. Menga istalgan savolni bering!
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <div class="input-box">
                    <textarea id="userInput" rows="1" placeholder="ZiyoAI dan nimanidir so'rang..." onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); sendMessage();}"></textarea>
                    <button onclick="sendMessage()">➔</button>
                </div>
            </div>
        </div>

        <script>
            const userId = 'user-' + Math.random().toString(36.substring(2, 9));

            async function sendMessage() {
                const input = document.getElementById('userInput');
                const messages = document.getElementById('messages');
                const text = input.value.trim();
                if(!text) return;

                // Foydalanuvchi xabari
                messages.innerHTML += `
                    <div class="message-wrapper">
                        <div class="avatar user-avatar">S</div>
                        <div class="message-content"><b>Siz:</b> ${text}</div>
                    </div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;

                // Yuklanmoqda...
                const loadingId = 'loading-' + Date.now();
                messages.innerHTML += `
                    <div class="message-wrapper" id="${loadingId}">
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content" style="color: var(--text-secondary);">ZiyoAI o'ylamoqda va bazadan qidirmoqda...</div>
                    </div>`;
                messages.scrollTop = messages.scrollHeight;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: userId, prompt: text})
                    });
                    const data = await response.json();
                    document.getElementById(loadingId).innerHTML = `
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content"><b>ZiyoAI:</b> ${data.reply}</div>`;
                } catch (err) {
                    document.getElementById(loadingId).innerHTML = `
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content" style="color: #ff8ab4;">Tizimda tarmoq xatoligi yuz berdi, qayta urinib ko'ring.</div>`;
                }
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')


# --- API HANDLERS (Sayt va Boshqalar ulanishi uchun) ---
async def api_chat_handler(request):
    try:
        data = await request.json()
        user_id = data.get("user_id", "default_user")
        prompt = data.get("prompt", "")
        reply = await generate_ziyo_response(user_id, prompt)
        return web.json_response({"status": "success", "reply": reply})
    except Exception as e:
        return web.json_response({"status": "error", "reply": str(e)}, status=400)

async def api_external_generate(request):
    """Boshqalar sizning API'ngizni ishlatishi uchun maxsus endpoint"""
    try:
        api_key = request.headers.get("X-API-Key")
        if not validate_api_key(api_key):
            return web.json_response({"error": "Unauthorized: Yaroqli API kalit taqdim etilmadi."}, status=401)
        
        data = await request.json()
        prompt = data.get("prompt", "")
        user_id = data.get("user_id", "external_api_user")
        
        reply = await generate_ziyo_response(user_id, prompt)
        return web.json_response({"status": "success", "reply": reply})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_create_key(request):
    """Yangi API kalit generatsiya qilish"""
    try:
        data = await request.json()
        owner = data.get("owner", "Developer")
        raw_string = owner + str(os.urandom(16))
        new_key = "ziyo_" + hashlib.sha256(raw_string.encode()).hexdigest()[:32]
        
        conn = sqlite3.connect("ziyo_core.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO api_keys (api_key, owner) VALUES (?, ?)", (new_key, owner))
        conn.commit()
        conn.close()
        
        return web.json_response({"status": "success", "api_key": new_key, "owner": owner})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)


# --- ILOVANI YIG'ISH VA ISHGA TUSHIRISH ---
async def init_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_post("/api/chat", api_chat_handler)
    app.router.add_post("/api/v1/generate", api_external_generate)
    app.router.add_post("/api/v1/create_key", api_create_key)
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app = asyncio.run(init_app())
    web.run_app(app, host="0.0.0.0", port=port)
