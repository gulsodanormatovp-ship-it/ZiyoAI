import asyncio
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# --- ZIYO-AI ASOSIY MLYA VA LOGIKASI ---
async def generate_ziyo_response(prompt: str) -> str:
    # Bu yerda ZiyoAI o'zining shaxsiy intellektual bazasi orqali javob shakllantiradi
    clean_prompt = prompt.lower()
    
    if "salom" in clean_prompt:
        return "Assalomu alaykum! Men ZiyoAI man. Sizga qanday ilmiy yoki texnik yordam bera olaman?"
    elif "python" in clean_prompt:
        return "Python — bu universal va kuchli dasturlash tili. ZiyoAI akademiyasida uni noldan o'rganishingiz mumkin!"
    else:
        return f"ZiyoAI tushundi: '{prompt}'. Bu savol bo'yicha shaxsiy bazamiz tahlil qilinmoqda va tez orada mukammal yechim taqdim etiladi!"

# --- VEB INTERFEYS VA CHAT SAHifASI ---
async def index_handler(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZiyoAI - Mustaqil Intellekt Markazi</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { width: 100%; max-width: 600px; background: #1e293b; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; height: 80vh; overflow: hidden; }
            .chat-header { background: #3b82f6; padding: 20px; font-size: 20px; font-weight: bold; text-align: center; }
            .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .message { padding: 12px 16px; border-radius: 12px; max-width: 80%; line-height: 1.5; }
            .user-message { background: #2563eb; align-self: flex-end; color: white; }
            .ai-message { background: #334155; align-self: flex-start; color: #f1f5f9; }
            .chat-input { display: flex; padding: 15px; background: #0f172a; border-top: 1px solid #334155; }
            .chat-input input { flex: 1; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #1e293b; color: white; outline: none; font-size: 16px; }
            .chat-input button { background: #3b82f6; color: white; border: none; padding: 0 20px; margin-left: 10px; border-radius: 8px; cursor: pointer; font-weight: bold; }
            .chat-input button:hover { background: #2563eb; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">✨ ZiyoAI Chat Markazi</div>
            <div class="chat-messages" id="messages">
                <div class="message ai-message">Salom! Men ZiyoAI man. Menga istalgan savolingizni bering.</div>
            </div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="Xabar yozing..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button onclick="sendMessage()">Yuborish</button>
            </div>
        </div>
        <script>
            async function sendMessage() {
                const input = document.getElementById('userInput');
                const messages = document.getElementById('messages');
                const text = input.value.trim();
                if(!text) return;
                
                messages.innerHTML += `<div class="message user-message">${text}</div>`;
                input.value = '';
                messages.scrollTop = messages.scrollHeight;
                
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: text})
                });
                const data = await response.json();
                
                messages.innerHTML += `<div class="message ai-message">${data.reply}</div>`;
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

# --- SERVERNI ISHGA TUSHIRISH ---
async def init_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_post("/api/chat", api_chat_handler)
    return app

if __name__ == "__main__":
    app = asyncio.run(init_app())
    port = int(os.environ.get("PORT", 10000)) if 'os' in globals() else 10000
    import os
    web.run_app(app, host="0.0.0.0", port=port)
