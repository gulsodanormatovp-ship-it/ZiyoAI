import asyncio
import logging
import os
import sqlite3
import hashlib
import urllib.parse
from aiohttp import web
from duckduckgo_search import DDGS

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

# --- BAZA VA XOTIRA TIZIMI (SQLite) ---
def init_db():
    conn = sqlite3.connect("ziyo_core.db")
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

def get_user_history(user_id: str):
    conn = sqlite3.connect("ziyo_core.db")
    cursor = conn.cursor()
    cursor.execute("SELECT role, content, timestamp FROM memory WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "time": r[2]} for r in rows]

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


# --- INTERNETDAN QIDIRISH MANTIG'I ---
def search_web(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                snippets = []
                for r in results:
                    title = r.get('title', '')
                    body = r.get('body', '')
                    snippets.append(f"<b>{title}</b><br>{body}")
                return "<br><br>".join(snippets)
    except Exception as e:
        logging.error(f"Web search error: {e}")
    return ""


# --- ASOSIY INTELLEKTUAL MARKAZ ---
async def generate_ziyo_response(user_id: str, prompt: str, image_data: str = None) -> str:
    text = prompt.lower().strip()
    
    # Agar rasm yuborilgan bo'lsa
    if image_data:
        save_message(user_id, "user", f"[Rasm yuborildi] {prompt}")
        reply = f"👁️ <b>ZiyoAI Vision Markazi:</b><br>Yuborilgan rasm qabul qilindi va tahlil qilindi. Rasm bo'yicha sizning so'rovingiz: <i>'{prompt if prompt else 'Tahlil qilish'}'</i>.<br><br><img src='{image_data}' alt='Uploaded Image' style='max-width:100%; border-radius:12px; margin-top:8px;'><br><span style='font-size: 10px; color: #888;'>ZiyoAI orqali yaratildi</span>"
        save_message(user_id, "assistant", reply)
        return reply

    save_message(user_id, "user", prompt)
    
    # 1. Video / Animatsiya yaratish moduli
    if any(w in text for w in ["video", "animatsiya", "kino", "klip", "gif"]):
        clean_prompt = prompt
        for word in ["video", "kino", "animatsiya", "klip", "gif", "chiz", "qil", "ber", "yarat"]:
            clean_prompt = clean_prompt.replace(word, "")
        clean_prompt = clean_prompt.strip(" ,.-!").strip()
        if not clean_prompt or len(clean_prompt) < 2:
            clean_prompt = "futuristic cinematic motion loop"

        encoded_prompt = urllib.parse.quote(f"animation {clean_prompt}, high quality")
        video_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
        
        reply = f"🎬 <b>ZiyoAI Video Markazi:</b><br>Siz talab qilgan <b>'{clean_prompt}'</b> mavzusida video/animatsiya tayyorlandi:<br><br><img src='{video_url}' alt='ZiyoAI Video' style='max-width:100%; border-radius:16px; margin-top:8px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);'><br><div style='font-size: 11px; color: #888; margin-top: 6px;'>ZiyoAI orqali yaratildi</div>"
        save_message(user_id, "assistant", reply)
        return reply

    # 2. Rasm yaratish moduli
    if any(w in text for w in ["rasm", "chiz", "generation", "image", "foto", "draw", "surat"]):
        clean_prompt = prompt
        for word in ["rasmini chiz", "rasm chiz", "chizib ber", "chiz", "rasm", "surat", "foto", "image", "yoki", "va"]:
            clean_prompt = clean_prompt.replace(word, "")
        
        clean_prompt = clean_prompt.split(".")[0].split("yoki")[0].strip(" ,.-!").strip()
        if not clean_prompt or len(clean_prompt) < 2:
            clean_prompt = "cyberpunk futuristic car"

        enhanced_prompt = f"{clean_prompt}, hyperrealistic, 8k resolution, cinematic lighting"
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
        
        reply = f"🎨 <b>ZiyoAI Dahshat Vizual Markazi:</b><br>Siz talab qilgan <b>'{clean_prompt}'</b> mavzusida rasm yaratildi:<br><br><img src='{image_url}' alt='ZiyoAI Generated Image' style='max-width:100%; border-radius:16px; margin-top:8px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);'><br><div style='font-size: 11px; color: #888; margin-top: 6px;'>ZiyoAI orqali yaratildi</div>"
        save_message(user_id, "assistant", reply)
        return reply

    # 3. Internetdan qidirish moduli
    if any(w in text for w in ["qidir", "internet", "yangilik", "kim", "nima", "qayerda", "ob-havo", "weather", "2026"]):
        search_result = search_web(prompt)
        if search_result:
            reply = f"🌐 <b>Internetdan topilgan ma'lumotlar:</b><br><br>{search_result}"
            save_message(user_id, "assistant", reply)
            return reply

    # 4. Oddiy muloqot
    if "salom" in text or "assalomu alaykum" in text:
        reply = "Assalomu alaykum! ZiyoAI tayyor. Nima chizib yoki video qilib berishimni xohlaysiz?"
    elif "python" in text:
        reply = "Python — eng kuchli dasturlash tili."
    elif "sen kimsan" in text or "ziyoai" in text:
        reply = "Men ZiyoAI man, mustaqil intellektual tizim."
    else:
        reply = f"ZiyoAI tahlil markazi: '{prompt}' bo'yicha so'rovingiz qabul qilindi!"

    save_message(user_id, "assistant", reply)
    return reply


# --- WEB INTERFEYS ---
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
            
            .sidebar { width: 280px; background: var(--sidebar-bg); display: flex; flex-direction: column; border-right: 1px solid var(--border-color); padding: 16px; z-index: 10; transition: 0.3s; justify-content: space-between; }
            .brand { font-size: 18px; font-weight: 700; color: #ffffff; margin-bottom: 24px; display: flex; align-items: center; gap: 10px; }
            .new-chat-btn { background: #282a2c; border: 1px solid var(--border-color); color: var(--text-color); padding: 12px; border-radius: 12px; cursor: pointer; text-align: left; font-size: 14px; transition: 0.2s; font-weight: 500; display: flex; align-items: center; gap: 8px; width: 100%; }
            .new-chat-btn:hover { background: var(--hover-bg); }
            
            .features-list { margin-top: 20px; display: flex; flex-direction: column; gap: 10px; font-size: 13px; color: var(--text-secondary); }
            .feature-item { padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.03); display: flex; align-items: center; gap: 10px; border: 1px solid rgba(255,255,255,0.05); }

            .api-box { background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); padding: 12px; border-radius: 12px; margin-top: 15px; }
            .api-box h4 { font-size: 13px; color: var(--accent-color); margin-bottom: 6px; }
            .api-input { width: 100%; background: #131314; border: 1px solid var(--border-color); color: #fff; padding: 6px; border-radius: 6px; font-size: 11px; margin-bottom: 8px; outline: none; }
            .api-btn { background: var(--accent-color); color: #131314; border: none; padding: 6px 10px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 11px; width: 100%; }
            .api-btn:hover { opacity: 0.9; }

            .main-container { flex: 1; display: flex; flex-direction: column; height: 100vh; background: var(--bg-color); position: relative; overflow: hidden; }
            .chat-header { padding: 16px 24px; border-bottom: 1px solid var(--border-color); font-size: 16px; font-weight: 600; color: #ffffff; display: flex; justify-content: space-between; align-items: center; background: var(--bg-color); }
            
            .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; width: 100%; max-width: 900px; margin: 0 auto; scroll-behavior: smooth; }
            .message-wrapper { display: flex; gap: 16px; width: 100%; line-height: 1.6; font-size: 15px; animation: fadeIn 0.3s ease; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
            
            .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; flex-shrink: 0; }
            .user-avatar { background: #5f6368; color: white; }
            .ai-avatar { background: linear-gradient(135deg, #8ab4f8, #c58af9); color: #131314; }
            .message-content { flex: 1; padding-top: 6px; word-break: break-word; color: var(--text-color); }
            
            .input-area { padding: 16px 20px 24px 20px; width: 100%; max-width: 900px; margin: 0 auto; background: var(--bg-color); }
            .input-box { display: flex; background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 24px; padding: 10px 16px; align-items: center; gap: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
            .input-box textarea { flex: 1; background: transparent; border: none; color: white; font-size: 15px; outline: none; resize: none; max-height: 150px; font-family: inherit; }
            
            .action-btn { background: transparent; border: none; color: var(--text-secondary); width: 38px; height: 38px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; font-size: 18px; }
            .action-btn:hover { background: var(--hover-bg); color: white; }
            .action-btn.listening { color: #ff5252; background: rgba(255,82,82,0.1); animation: pulse 1.5s infinite; }
            
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

            .send-btn { background: var(--accent-color); color: #131314; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; transition: 0.2s; flex-shrink: 0; }
            .send-btn:hover { opacity: 0.9; transform: scale(1.05); }

            #imagePreview { max-height: 60px; border-radius: 8px; display: none; margin-bottom: 5px; }

            @media (max-width: 768px) {
                .sidebar { display: none; }
                .chat-messages { padding: 15px; gap: 16px; }
                .input-area { padding: 10px 15px 20px 15px; }
            }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div>
                <div class="brand">✨ ZiyoAI Platform</div>
                <button class="new-chat-btn" onclick="startNewChat()"><span>+</span> Yangi suhbat</button>
                
                <div class="features-list">
                    <div class="feature-item">🧠 Saqlanadigan Xotira</div>
                    <div class="feature-item">🌐 Real vaqtda Qidiruv</div>
                    <div class="feature-item">🎨 Rasm & Video Yaratish</div>
                    <div class="feature-item">👁️ Rasm tahlili (OCR/Vision)</div>
                </div>
            </div>

            <div class="api-box">
                <h4>🔑 API Kalit Markazi</h4>
                <input type="text" id="apiKeyField" class="api-input" placeholder="Kalitni olish uchun bosing..." readonly>
                <button class="api-btn" onclick="generateApiKey()">API Kalit Olish</button>
            </div>
        </div>
        
        <div class="main-container">
            <div class="chat-header">
                <span>ZiyoAI Markaziy Tizimi v8.0</span>
                <span style="font-size: 12px; color: var(--accent-color); background: rgba(138,180,248,0.1); padding: 4px 12px; border-radius: 20px; border: 1px solid rgba(138,180,248,0.2);">To'liq funksional</span>
            </div>
            
            <div class="chat-messages" id="messages"></div>
            
            <div class="input-area">
                <img id="imagePreview" src="" alt="Preview">
                <div class="input-box">
                    <input type="file" id="imageInput" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">
                    <button class="action-btn" onclick="document.getElementById('imageInput').click()" title="Rasm yuklash">📷</button>
                    <button class="action-btn" id="micBtn" onclick="toggleSpeechRecognition()" title="Ovoz bilan gaplashish">🎤</button>
                    <textarea id="userInput" rows="1" placeholder="Xabar yozing yoki rasm yuklang..." onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); sendMessage();}"></textarea>
                    <button class="send-btn" onclick="sendMessage()">➔</button>
                </div>
            </div>
        </div>

        <script>
            let userId = localStorage.getItem('ziyo_user_id');
            if (!userId) {
                userId = 'user-' + Math.random().toString(36).substring(2, 9);
                localStorage.setItem('ziyo_user_id', userId);
            }

            let recognition;
            let isListening = false;
            let currentImageBase64 = null;

            // Suhbat tarixini yuklab kelish
            async function loadHistory() {
                try {
                    const res = await fetch(`/api/history?user_id=${userId}`);
                    const data = await res.json();
                    const messagesDiv = document.getElementById('messages');
                    messagesDiv.innerHTML = '';
                    
                    if (data.history && data.history.length > 0) {
                        data.history.forEach(msg => {
                            const isUser = msg.role === 'user';
                            messagesDiv.innerHTML += `
                                <div class="message-wrapper">
                                    <div class="avatar ${isUser ? 'user-avatar' : 'ai-avatar'}">${isUser ? 'S' : 'Z'}</div>
                                    <div class="message-content"><b>${isUser ? 'Siz' : 'ZiyoAI'}:</b> ${msg.content}</div>
                                </div>`;
                        });
                    } else {
                        messagesDiv.innerHTML += `
                            <div class="message-wrapper">
                                <div class="avatar ai-avatar">Z</div>
                                <div class="message-content"><b>ZiyoAI:</b> Assalomu alaykum! Xush kelibsiz. Yozishmalaringiz saqlanib boradi.</div>
                            </div>`;
                    }
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                } catch(e) {
                    console.error("Tarixni yuklashda xatolik:", e);
                }
            }

            loadHistory();

            function startNewChat() {
                localStorage.removeItem('ziyo_user_id');
                userId = 'user-' + Math.random().toString(36).substring(2, 9);
                localStorage.setItem('ziyo_user_id', userId);
                loadHistory();
            }

            function handleImageUpload(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        currentImageBase64 = e.target.result;
                        const preview = document.getElementById('imagePreview');
                        preview.src = currentImageBase64;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(file);
                }
            }

            async function generateApiKey() {
                try {
                    const res = await fetch('/api/v1/create_key', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({owner: 'Web User'})
                    });
                    const data = await res.json();
                    if (data.status === 'success') {
                        document.getElementById('apiKeyField').value = data.api_key;
                        alert("Yangi API kalitingiz muvaffaqiyatli yaratildi!");
                    }
                } catch(e) {
                    alert("API kalit yaratishda xatolik yuz berdi.");
                }
            }

            function toggleSpeechRecognition() {
                const micBtn = document.getElementById('micBtn');
                const input = document.getElementById('userInput');

                if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                    alert("Brauzeringiz ovozli qidirishni qo'llab-quvvatlamaydi.");
                    return;
                }

                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                if (isListening) {
                    recognition.stop();
                    return;
                }

                recognition = new SpeechRecognition();
                recognition.lang = 'uz-UZ';
                recognition.interimResults = false;
                recognition.maxAlternatives = 1;

                recognition.onstart = () => {
                    isListening = true;
                    micBtn.classList.add('listening');
                    input.placeholder = "Eshitayapman, gapiring...";
                };

                recognition.onresult = (event) => {
                    const speechText = event.results[0][0].transcript;
                    input.value = speechText;
                    sendMessage();
                };

                recognition.onerror = () => { stopListeningState(); };
                recognition.onend = () => { stopListeningState(); };
                recognition.start();
            }

            function stopListeningState() {
                isListening = false;
                document.getElementById('micBtn').classList.remove('listening');
                document.getElementById('userInput').placeholder = "Xabar yozing yoki rasm yuklang...";
            }

            function speakText(text) {
                if ('speechSynthesis' in window) {
                    const cleanText = text.replace(/<[^>]*>?/gm, '');
                    const utterance = new SpeechSynthesisUtterance(cleanText);
                    utterance.lang = 'uz-UZ';
                    utterance.rate = 1.0;
                    window.speechSynthesis.speak(utterance);
                }
            }

            async function sendMessage() {
                const input = document.getElementById('userInput');
                const messages = document.getElementById('messages');
                const text = input.value.trim();
                
                if(!text && !currentImageBase64) return;

                let userDisplayContent = text;
                if (currentImageBase64) {
                    userDisplayContent += `<br><img src="${currentImageBase64}" style="max-height:120px; border-radius:8px; margin-top:5px;">`;
                }

                messages.innerHTML += `
                    <div class="message-wrapper">
                        <div class="avatar user-avatar">S</div>
                        <div class="message-content"><b>Siz:</b> ${userDisplayContent}</div>
                    </div>`;
                
                const imgToSend = currentImageBase64;
                input.value = '';
                currentImageBase64 = null;
                document.getElementById('imagePreview').style.display = 'none';
                messages.scrollTop = messages.scrollHeight;

                const loadingId = 'loading-' + Date.now();
                messages.innerHTML += `
                    <div class="message-wrapper" id="${loadingId}">
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content" style="color: var(--text-secondary);">ZiyoAI tahlil qilmoqda...</div>
                    </div>`;
                messages.scrollTop = messages.scrollHeight;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_id: userId, prompt: text, image: imgToSend})
                    });
                    const data = await response.json();
                    
                    document.getElementById(loadingId).innerHTML = `
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content"><b>ZiyoAI:</b> ${data.reply}</div>`;
                    
                    speakText(data.reply);

                } catch (err) {
                    document.getElementById(loadingId).innerHTML = `
                        <div class="avatar ai-avatar">Z</div>
                        <div class="message-content" style="color: #ff8ab4;">Tarmoqda xatolik yuz berdi.</div>`;
                }
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')


# --- API HANDLERS ---
async def api_history_handler(request):
    user_id = request.query.get("user_id", "default_user")
    history = get_user_history(user_id)
    return web.json_response({"status": "success", "history": history})

async def api_chat_handler(request):
    try:
        data = await request.json()
        user_id = data.get("user_id", "default_user")
        prompt = data.get("prompt", "")
        image_data = data.get("image", None)
        
        reply = await generate_ziyo_response(user_id, prompt, image_data)
        return web.json_response({"status": "success", "reply": reply})
    except Exception as e:
        return web.json_response({"status": "error", "reply": str(e)}, status=400)

async def api_external_generate(request):
    try:
        api_key = request.headers.get("X-API-Key")
        if not validate_api_key(api_key):
            return web.json_response({"error": "Unauthorized: Yaroqli API kalit topilmadi."}, status=401)
        
        data = await request.json()
        prompt = data.get("prompt", "")
        user_id = data.get("user_id", "external_api_user")
        image_data = data.get("image", None)
        
        reply = await generate_ziyo_response(user_id, prompt, image_data)
        return web.json_response({"status": "success", "reply": reply})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def api_create_key(request):
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


# --- ILOVANI ISHGA TUSHIRISH ---
async def init_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/history", api_history_handler)
    app.router.add_post("/api/chat", api_chat_handler)
    app.router.add_post("/api/v1/generate", api_external_generate)
    app.router.add_post("/api/v1/create_key", api_create_key)
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app = asyncio.run(init_app())
    web.run_app(app, host="0.0.0.0", port=port)
