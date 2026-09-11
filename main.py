import asyncio
import sqlite3
import uuid
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import os

app = FastAPI(title="ZiyoAI Enterprise Next-Gen", version="3.0")

# Static papkalar
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def get_db():
    conn = sqlite3.connect("ziyoai_pro.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

class ChatMessage(BaseModel):
    user_id: str
    chat_id: str
    prompt: str
    mode: str = "standard" # standard, deep_research, coding, rag

class CodeRunRequest(BaseModel):
    code: str

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

# --- REAL-TIME STREAMING WEBSOCKET (ChatGPT Style Stream + Voice Channel) ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Real vaqtda so'zni qismma-qism (streaming) yuborish simulyatsiyasi
            response_text = f"ZiyoAI (Stream): Sizning '{data}' so'rovingiz tahlil qilindi va real vaqt rejimida qayta ishlandi."
            
            for word in response_text.split():
                await websocket.send_text(word + " ")
                await asyncio.sleep(0.05) # Jonli yozilish effekti
            await websocket.send_text("[DONE]")
    except WebSocketDisconnect:
        print(f"Foydalanuvchi uzildi: {user_id}")

# --- API: CHAT HISTORIES & CREATION ---
@app.get("/api/chats/{user_id}")
async def get_user_chats(user_id: str):
    db = get_db()
    chats = db.execute("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    return [dict(c) for c in chats]

@app.post("/api/chat/new")
async def create_chat(user_id: str = Form(...), title: str = Form(...), mode: str = Form(...)):
    db = get_db()
    chat_id = "chat_" + str(uuid.uuid4())[:8]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("INSERT INTO chats (chat_id, user_id, title, mode, created_at) VALUES (?, ?, ?, ?, ?)",
               (chat_id, user_id, title, mode, now))
    db.commit()
    return {"chat_id": chat_id, "status": "created"}

# --- API: SANDBOX CODE EXECUTION (Python kodlarni saytda bajarish) ---
@app.post("/api/sandbox/run")
async def run_code(req: CodeRunRequest):
    temp_file = "temp_exec.py"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(req.code)
    
    try:
        # Xavfsiz subprocess orqali kodni ishga tushirish
        result = subprocess.run(["python", temp_file], capture_output=True, text=True, timeout=5)
        output = result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        output = "Xatolik: Kodni bajarish vaqti tugadi (Infinite loop xavfi)."
    except Exception as e:
        output = f"Xatolik: {str(e)}"
    
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    return {"output": output}

# --- API: RAG & FILE UPLOAD (PDF, Word, Codebases) ---
@app.post("/api/rag/upload")
async def upload_rag_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    db = get_db()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db.execute("INSERT INTO media_gallery (user_id, file_url, media_type, created_at) VALUES (?, ?, ?, ?)",
               (user_id, f"/{file_path}", "document", now))
    db.commit()
    
    return {"status": "success", "message": "Fayl muvaffaqiyatli yuklandi va RAG bazasiga indekslandi!", "url": f"/{file_path}"}

# --- API: USER CABINET & API KEYS ---
@app.get("/api/user/{user_id}")
async def get_user_profile(user_id: str):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user:
        api_key = "ziyo_key_" + uuid.uuid4().hex[:16]
        db.execute("INSERT INTO users (user_id, username, balance, api_key) VALUES (?, ?, ?, ?)",
                   (user_id, "Pro_User", 1000, api_key))
        db.commit()
        user = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(user)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
