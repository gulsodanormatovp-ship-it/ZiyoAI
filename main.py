import asyncio
import logging
import os
import sqlite3
import urllib.parse
from aiohttp import web
from duckduckgo_search import DDGS

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

logging.basicConfig(level=logging.INFO)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY and AsyncGroq:
    groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    logging.info("Groq mijoz ishga tushdi.")
else:
    groq_client = None

DB_NAME = "ziyo_core.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE,
            owner TEXT,
            requests_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1
        )
    """)
    cursor.execute("SELECT api_key FROM api_keys WHERE owner = 'Admin' LIMIT 1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO api_keys (api_key, owner) VALUES (?, ?)", ("ziyo_admin_dev_key", "Admin"))
    conn.commit()
    conn.close()

init_db()

def save_message(user_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memory (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(user_id: str, limit: int = 10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM memory WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows[::-1]]

def validate_api_key(api_key: str) -> bool:
    if not api_key or not api_key.startswith("ziyo_"):
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM api_keys WHERE api_key = ? AND is_active = 1", (api_key,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE api_keys SET requests_count = requests_count + 1 WHERE api_key = ?", (api_key,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def search_web_sync(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                snippets = []
                for r in results:
                    snippets.append(f"<b>{r.get('title')}</b><br>{r.get('body')}")
                return "<br><br>".join(snippets)
    except Exception as e:
        logging.error(f"DDGS Error: {e}")
    return "Kechirasiz, internetdan ma'lumot topilmadi."

async def get_ai_response(user_id: str, prompt: str) -> str:
    text = prompt.lower().strip()
    save_message(user_id, "user", prompt)

    if any(w in text for w in ["rasm", "chiz", "draw", "image", "surat"]):
        clean_prompt = prompt.replace("rasmini chiz", "").replace("rasm chiz", "").replace("chizib ber", "").strip(" ,.")
        encoded_prompt = urllib.parse.quote(clean_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true"
        reply = f"🎨 <b>ZiyoAI Vizual Markazi:</b><br>Siz so'ragan rasm: <i>{clean_prompt}</i><br><br><img src='{image_url}' style='max-width:100%; border-radius:10px;'>"
        save_message(user_id, "assistant", reply)
        return reply

    if any(w in text for w in ["qidir", "internet", "yangilik", "nima bu", "kim"]) or text.startswith(("qachon", "qayerda")):
        search_results = await asyncio.to_thread(search_web_sync, prompt)
        reply = f"🌐 <b>Internetdan topilgan ma'lumotlar:</b><br><br>{search_results}"
        save_message(user_id, "assistant", reply)
        return reply

    if groq_client:
        try:
            history = get_chat_history(user_id)
            messages = [
                {"role": "system", "content": "Siz ZiyoAI ismli aqlli yordamchisiz. O'zbekistonlik dasturchi tomonidan yaratilgansiz. O'zbek tilida mukammal javob bering."},
            ] + history + [{"role": "user", "content": prompt}]

            chat_completion = await groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1000
            )
            reply = chat_completion.choices[0].message.content
        except Exception as e:
            logging.error(f"Groq Error: {e}")
            reply = f"Kechirasiz, sun'iy intellekt javob berishda xatolikka uchradi: {str(e)}"
    else:
        reply = "ZiyoAI faqat rasm chizish va qidirish rejimida (Groq kaliti ulanmagan)."

    save_message(user_id, "assistant", reply)
    return reply

INDEX_HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZiyoAI Platformasi</title>
    <style>
        * { box-sizing: border-box; }
        :root {
            --bg-color: #121212;
            --chat-bg: #1e1e1e;
            --sidebar-bg: #181818;
            --text-color: #f1f1f1;
            --accent-color: #10a37f;
            --user-msg: #2f3238;
            --ai-msg: #212327;
            --border-color: #333;
        }
        body { margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--bg-color); color: var(--text-color); display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 280px; background-color: var(--sidebar-bg); display: flex; flex-direction: column; padding: 20px; border-right: 1px solid var(--border-color); flex-shrink: 0; transition: 0.3s; z-index: 100; }
        .sidebar h2 { color: var(--accent-color); margin-top: 0; text-align: center; font-size: 22px; }
        .menu-btn { background: #222; border: 1px solid var(--border-color); color: var(--text-color); padding: 12px; margin-bottom: 10px; border-radius: 8px; cursor: pointer; text-align: left; font-size: 14px; transition: 0.2s; }
        .menu-btn:hover { background: #2a2a2a; }
        
        .api-section { margin-top: auto; border-top: 1px solid var(--border-color); padding-top: 15px; }
        .api-section p { font-size: 13px; color: #aaa; margin-bottom: 5px; }
        .api-key-box { background: #000; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; word-break: break-all; color: var(--accent-color); margin-bottom: 10px; border: 1px solid var(--border-color); }
        #getApiBtn { background-color: var(--accent-color); color: white; border: none; width: 100%; padding: 10px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        #getApiBtn:hover { opacity: 0.9; }

        .main-chat { flex: 1; display: flex; flex-direction: column; background-color: var(--chat-bg); height: 100vh; position: relative; }
        .chat-header { padding: 15px 20px; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; font-weight: bold; background: var(--sidebar-bg); }
        #menu-toggle { display: none; font-size: 20px; background: none; border: none; color: var(--text-color); cursor: pointer; margin-right: 15px; }
        
        .chat-history { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        
        .message { max-width: 75%; padding: 14px 18px; border-radius: 12px; line-height: 1.5; font-size: 14.5px; word-wrap: break-word; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .message.user { align-self: flex-end; background-color: var(--user-msg); border-bottom-right-radius: 3px; }
        .message.ai { align-self: flex-start; background-color: var(--ai-msg); border-bottom-left-radius: 3px; border: 1px solid var(--border-color); }
        .message strong { display: block; margin-bottom: 4px; font-size: 12px; opacity: 0.7; }
        .message img { margin-top: 10px; border-radius: 8px; max-width: 100%; }

        .input-area { padding: 15px 20px; background-color: var(--sidebar-bg); border-top: 1px solid var(--border-color); display: flex; gap: 10px; align-items: center; }
        #user-input { flex: 1; padding: 12px 15px; border-radius: 8px; border: 1px solid var(--border-color); background-color: #222; color: white; resize: none; outline: none; font-size: 14px; max-height: 120px; }
        #user-input:focus { border-color: var(--accent-color); }
        #send-btn { background-color: var(--accent-color); color: white; border: none; padding: 12px 22px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; height: 46px; flex-shrink: 0; }
        #send-btn:hover { opacity: 0.9; }

        @media (max-width: 768px) {
            .sidebar { position: fixed; left: 0; top: 0; bottom: 0; transform: translateX(-100%); }
            .sidebar.active { transform: translateX(0); }
            #menu-toggle { display: block; }
            .message { max-width: 90%; }
        }
    </style>
</head>
<body>
<div class="sidebar" id="sidebar">
    <h2>ZiyoAI</h2>
    <button class="menu-btn" onclick="startNewChat()">+ Yangi suhbat</button>
    <div class="menu-btn">🧠 Xotira: Yoqilgan</div>
    <div class="menu-btn">🌐 Qidiruv: Yoqilgan</div>
    <div class="menu-btn">🎨 Rasm: Yoqilgan</div>
    <div class="api-section">
        <p>Sizning API kalitingiz:</p>
        <div class="api-key-box" id="my-api-key">ziyo_admin_dev_key</div>
        <button id="getApiBtn" onclick="promptApiKey()">API Kalitni Olish</button>
    </div>
</div>
<div class="main-chat">
    <div class="chat-header">
        <button id="menu-toggle" onclick="toggleSidebar()">☰</button>
        ZiyoAI Markaziy Tizimi
    </div>
    <div class="chat-history" id="chat-history">
        <div class="message ai">
            <strong>ZiyoAI:</strong> Assalomu alaykum! Men ZiyoAI yordamchisiman. Sizga qanday yordam bera olaman?
        </div>
    </div>
    <div class="input-area">
        <textarea id="user-input" placeholder="Xabar yozing..." rows="1" onkeydown="handleKeyPress(event)"></textarea>
        <button id="send-btn" onclick="sendMessage()">Yuborish</button>
    </div>
</div>
<script>
    const userId = 'user_' + Math.random().toString(36).substring(2, 9);
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');

    function toggleSidebar() {
        document.getElementById('sidebar').classList.toggle('active');
    }

    function startNewChat() {
        chatHistory.innerHTML = '<div class="message ai"><strong>ZiyoAI:</strong> Yangi suhbat boshlandi. Qanday yordam bera olaman?</div>';
    }

    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if(!text) return;
        
        chatHistory.innerHTML += `<div class="message user"><strong>Siz</strong>${text}</div>`;
        userInput.value = '';
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            let response = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({user_id: userId, prompt: text})
            });
            let data = await response.json();
            chatHistory.innerHTML += `<div class="message ai"><strong>ZiyoAI</strong>${data.reply}</div>`;
            chatHistory.scrollTop = chatHistory.scrollHeight;
        } catch(e) {
            chatHistory.innerHTML += `<div class="message ai"><strong>ZiyoAI</strong>Xatolik yuz berdi.</div>`;
        }
    }

    function promptApiKey() {
        fetch('/api/v1/create_key', {method: 'POST'})
        .then(res => res.json())
        .then(data => {
            document.getElementById('my-api-key').innerText = data.api_key;
            alert("Yangi API kalitingiz yaratildi: " + data.api_key);
        });
    }
</script>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=INDEX_HTML, content_type='text/html')

async def handle_chat(request):
    try:
        data = await request.json()
        user_id = data.get("user_id", "default_user")
        prompt = data.get("prompt", "")
        if not prompt:
            return web.json_response({"reply": "Bo'sh xabar yubordingiz."})
        
        reply = await get_ai_response(user_id, prompt)
        return web.json_response({"reply": reply})
    except Exception as x:
        return web.json_response({"reply": f"Xatolik: {str(x)}"})

async def handle_api_generate(request):
    api_key = request.headers.get("X-API-Key")
    if not validate_api_key(api_key):
        return web.json_response({"error": "Unauthorized: Yaroqsiz yoki mavjud bo'lmagan API kalit."}, status=401)
    
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        user_id = data.get("user_id", "api_user")
        if not prompt:
            return web.json_response({"error": "Prompt kiritilmadi."}, status=400)
        
        reply = await get_ai_response(user_id, prompt)
        return web.json_response({"status": "success", "reply": reply})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_create_key(request):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    import uuid
    new_key = "ziyo_" + uuid.uuid4().hex[:16]
    cursor.execute("INSERT INTO api_keys (api_key, owner) VALUES (?, ?)", (new_key, "Web User"))
    conn.commit()
    conn.close()
    return web.json_response({"api_key": new_key})

app = web.Application()
app.router.add_get('/', handle_index)
app.router.add_post('/chat', handle_chat)
app.router.add_post('/api/v1/generate', handle_api_generate)
app.router.add_post('/api/v1/create_key', handle_create_key)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host='0.0.0.0', port=port)
