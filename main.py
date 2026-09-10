import asyncio
import logging
import os
import json
from aiohttp import web

logging.basicConfig(level=logging.INFO)

async def generate_ziyo_response(prompt: str) -> str:
    text = prompt.lower().strip()
    
    if any(w in text for w in ["salom", "assalomu alaykum", "hi", "hello"]):
        return "Assalomu alaykum! Men ZiyoAI — sizning shaxsiy mustaqil intellektual tizimingizman. Bugun sizga qanday ilmiy, texnik yoki ijodiy yo'nalishda yordam bera olaman?"
    elif "python" in text:
        return "Python — bu yuqori darajadagi, o'rganish uchun qulay va juda qudratli dasturlash tili. U veb-dasturlash (FastAPI, Django), sun'iy intellekt, ma'lumotlar tili va avtomatlashtirishda yetakchi o'rinda turadi. ZiyoAI orqali siz o'z Python loyihalaringizni mukammal darajada rivojlantirishingiz mumkin."
    elif "dasturlash" in text or "kod" in text:
        return "Dasturlash — kelajak kasbi. O'z g'oyangizni kodga ko'chirish uchun avvalo mantiqni to'g'ri tuzib olish va to'g'ri texnologiyalarni tanlash muhim. Qanday dastur yaratmoqchisiz? Keling, uni birgalikda rejalashtiramiz."
    elif "koinot" in text or "yulduz" in text or "fazo" in text:
        return "Koinotimiz cheksiz kengliklarga ega. Faqatgina bizning Somon Yo'li galaktikasining o'zida yuz milliarddan ortiq yulduzlar mavjud. Butun kuzatiladigan koinotda esa trillionlab galaktikalar bor deb taxmin qilinadi. ZiyoAI koinot sirlarini o'rganishda doim siz bilan!"
    elif "fizika" in text or "elm" in text:
        return "Ilm-fan olami doimiy harakatda. Fizika olam qonunlarini (kvant mexanikasi, nisbiylik nazariyasi) tushuntirsa, texnologiya ularni hayotga tatbiq etadi. Qaysi ilmiy mavzu sizni qiziqtiryapti?"
    elif "ziyoai" in text or "sen kimsan" in text:
        return "Men — ZiyoAIman. Hech qanday tashqi uchinchi tomon API xizmatlariga bog'lanmagan, to'liq mustaqil, o'zimizning serverimizda ishlaydigan intellektual tizimman."
    else:
        return f"ZiyoAI tahlil markazi: '{prompt}' bo'yicha so'rovingiz qabul qilindi. Ushbu mavzu bo'yicha ma'lumotlar bazamiz ishga tushdi: bu yo'nalishda asosiy e'tiborni tizimli yondashuv va to'g'ri algoritmga qaratish lozim. Sizga aniqroq kod, matn yoki reja tuzib berishim uchun savolingizni biroz aniqroq yozib yuboring!"

async def index_handler(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZiyoAI - Mustaqil Intellektual Tizim</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #131314; color: #e3e3e3; display: flex; height: 100vh; overflow: hidden; }
            .sidebar { width: 260px; background: #1e1f20; display: flex; flex-direction: column; border-right: 1px solid #2d2e30; padding: 20px; }
            .brand { font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 30px; display: flex; align-items: center; gap: 10px; }
            .new-chat-btn { background: #282a2c; border: 1px solid #3c4043; color: #e3e3e3; padding: 12px; border-radius: 12px; cursor: pointer; text-align: left; font-size: 14px; transition: 0.2s; }
            .new-chat-btn:hover { background: #37393b; }
            .main-container { flex: 1; display: flex; flex-direction: column; height: 100vh; background: #131314; }
            .chat-header { padding: 15px 30px; border-bottom: 1px solid #2d2e30; font-size: 18px; font-weight: 600; color: #ffffff; background: #131314; }
            .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; max-width: 800px; width: 100%; margin: 0 auto; }
            .message { display: flex; gap: 15px; padding: 15px; border-radius: 12px; line-height: 1.6; font-size: 15px; }
            .user-message { background: #1e1f20; align-self: stretch; border: 1px solid #2d2e30; }
            .ai-message { background: #131314; align-self: stretch; color: #c4c7c5; }
            .input-area { padding: 20px; max-width: 800px; width: 100%; margin: 0 auto; background: #131314; }
            .input-box { display: flex; background: #1e1f20; border: 1px solid #3c4043; border-radius: 16px; padding: 10px 15px; align-items: center; }
            .input-box textarea { flex: 1; background: transparent; border: none; color: white; font-size: 16px; outline: none; resize: none; max-height: 150px; font-family: inherit; }
            .input-box button { background: #8ab4f8; color: #131314; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-weight: bold; transition: 0.2s; }
            .input-box button:hover { background: #aecbfa; }
            @media (max-width: 768px) { .sidebar { display: none; } }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="brand">✨ ZiyoAI</div>
            <button class="new-chat-btn" onclick="location.reload()">+ Yangi suhbat</button>
        </div>
        <div class="main-container">
            <div class="chat-header">ZiyoAI Markaziy Tizimi</div>
            <div class="chat-messages" id="messages">
                <div class="message ai-message">
                    <b>ZiyoAI:</b> Assalomu alaykum! Men to'liq mustaqil ZiyoAI tiziman. Menga istalgan mavzuda savol bering.
                </div>
            </div>
            <div class="input-area">
                <div class="input-box">
                    <textarea id="userInput" rows="1" placeholder="ZiyoAI dan nimanidir so'rang..." onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault(); sendMessage();}"></textarea>
                    <button onclick="sendMessage()">Yuborish</button>
                </div>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const messages = document.getElementById('messages');
                const text = input.value.trim();
                if(!text) return;
                messages.innerHTML += `<div class="message user-message"><b>Siz:</b> ${text}</div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;
                const loadingId = 'loading-' + Date.now();
                messages.innerHTML += `<div class="message ai-message" id="${loadingId}"><b>ZiyoAI:</b> Javob tayyorlanmoqda...</div>`;
                messages.scrollTop = messages.scrollHeight;
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt: text})
                    });
                    const data = await response.json();
                    document.getElementById(loadingId).innerHTML = `<b>ZiyoAI:</b> ${data.reply}`;
                } catch (err) {
                    document.getElementById(loadingId).innerHTML = `<b>ZiyoAI:</b> Tizimda kichik uzilish bo'ldi, qayta urinib ko'ring.`;
                }
                messages.scrollTop = messages.scrollHeight;
            }
        </script>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def api_chat_handler(request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        reply = await generate_ziyo_response(prompt)
        return web.json_response({"reply": reply})
    except Exception as e:
        return web.json_response({"reply": f"Xatolik yuz berdi: {str(e)}"})

async def init_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_post("/api/chat", api_chat_handler)
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app = asyncio.run(init_app())
    web.run_app(app, host="0.0.0.0", port=port)
