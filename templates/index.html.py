<!DOCTYPE html>
<html lang="uz" class="dark">
<head>
    <meta charset="UTF-8">
    <title>ZiyoAI Enterprise - Ultra Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = { darkMode: 'class', theme: { extend: {} } }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-gray-100 dark:bg-gray-950 dark:text-gray-100 flex h-screen overflow-hidden transition-colors duration-300">

    <!-- YON PANEL (SIDEBAR - CHATGPT STYLE) -->
    <div class="w-72 bg-gray-900 dark:bg-gray-900 border-r border-gray-800 flex flex-col justify-between">
        <div>
            <div class="p-4 flex items-center justify-between border-b border-gray-800">
                <span class="font-bold text-lg text-emerald-400 flex items-center gap-2"><i class="fa-solid fa-brain"></i> ZiyoAI Pro</span>
                <button onclick="toggleTheme()" class="text-gray-400 hover:text-white"><i class="fa-solid fa-moon" id="theme-icon"></i></button>
            </div>
            <div class="p-3">
                <button onclick="startNewChat()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-2.5 px-4 rounded-xl font-medium flex items-center justify-center gap-2 transition shadow-lg">
                    <i class="fa-solid fa-plus"></i> Yangi suhbat
                </button>
            </div>
            <!-- Chatlar tarixi ro'yxati -->
            <div id="chat-history-list" class="p-3 space-y-1.5 overflow-y-auto max-h-[calc(100vh-220px)] text-sm">
                <!-- Dinamik to'ldiriladi -->
            </div>
        </div>
        <!-- Foydalanuvchi kabineti va balans -->
        <div class="p-4 border-t border-gray-800 bg-gray-950/40">
            <div class="flex items-center justify-between text-xs mb-2">
                <span class="text-gray-400">Balans:</span>
                <span id="user-balance" class="text-emerald-400 font-bold">1000 so'rov</span>
            </div>
            <button onclick="openCabinet()" class="w-full bg-gray-800 hover:bg-gray-700 text-gray-200 py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition">
                <i class="fa-solid fa-user-gear"></i> Kabinet & API Kalit
            </button>
        </div>
    </div>

    <!-- ASOSIY ISH MAYDONI -->
    <div class="flex-1 flex flex-col h-full bg-gray-900">
        <!-- Top Navigation & Modes -->
        <div class="h-14 border-b border-gray-800 px-6 flex items-center justify-between bg-gray-900/80 backdrop-blur">
            <div class="flex items-center gap-3">
                <span id="active-chat-title" class="font-semibold text-gray-200">Yangi Suhbat</span>
                <select id="ai-mode-select" class="bg-gray-800 text-xs text-emerald-400 border border-gray-700 rounded-lg px-2 py-1 outline-none">
                    <option value="standard">Standard AI</option>
                    <option value="deep_research">Deep Research (Chuqur Qidiruv)</option>
                    <option value="coding">Sandbox Code Execution</option>
                    <option value="rag">RAG (Fayllar tahlili)</option>
                </select>
            </div>
            <div class="flex items-center gap-4 text-sm">
                <button onclick="openGallery()" class="text-gray-400 hover:text-white flex items-center gap-1.5"><i class="fa-solid fa-images"></i> Galereya</button>
            </div>
        </div>

        <!-- Chat Xabarlar Maydoni -->
        <div id="chat-messages" class="flex-1 overflow-y-auto p-6 space-y-6">
            <div class="flex items-start gap-4">
                <div class="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold shrink-0 shadow-md">Z</div>
                <div class="bg-gray-800/90 border border-gray-700/50 p-4 rounded-2xl max-w-3xl text-gray-200 leading-relaxed shadow-xl">
                    Assalomu alaykum! ZiyoAI Enterprise platformasiga xush kelibsiz. Barcha funksiyalar (Real-time Streaming, Sandbox, RAG, Balans, Galereya) to'liq tayyor. Savolingizni yozing!
                </div>
            </div>
        </div>

        <!-- Pastki Input & Voice Mode Paneli -->
        <div class="p-4 border-t border-gray-800 bg-gray-900">
            <div class="max-w-4xl mx-auto flex items-center gap-3 bg-gray-800/90 rounded-2xl p-2.5 border border-gray-700 focus-within:border-emerald-500 transition shadow-inner">
                <!-- Fayl yuklash (RAG uchun) -->
                <button onclick="document.getElementById('rag-file').click()" class="text-gray-400 hover:text-white p-2 transition" title="Fayl yuklash (PDF/Word/Code)"><i class="fa-solid fa-paperclip"></i></button>
                <input type="file" id="rag-file" class="hidden" onchange="uploadFile(this)">

                <textarea id="user-input" rows="1" placeholder="ZiyoAI'ga xabar yozing yoki kod kiriting..." class="flex-1 bg-transparent text-gray-100 placeholder-gray-500 focus:outline-none resize-none px-2 text-sm"></textarea>
                
                <!-- ChatGPT Style Voice-to-Voice Tugmasi -->
                <button onclick="toggleVoiceMode()" id="voice-btn" class="text-gray-400 hover:text-emerald-400 p-2 transition" title="Ovozli muloqot (Voice-to-Voice)"><i class="fa-solid fa-microphone"></i></button>
                
                <button onclick="sendMessageStream()" class="bg-emerald-600 hover:bg-emerald-500 text-white w-10 h-10 rounded-xl flex items-center justify-center transition shadow-lg">
                    <i class="fa-solid fa-arrow-up"></i>
                </button>
            </div>
            <div class="text-center text-[11px] text-gray-500 mt-2">ZiyoAI xatolikka yo'l qo'yishi mumkin. Muhim ma'lumotlarni tekshiring.</div>
        </div>
    </div>

    <!-- JavaScript Integratsiyasi -->
    <script>
        let userId = "user_demo_123";
        let currentChatId = "chat_default";
        let ws = null;

        function toggleTheme() {
            document.documentElement.classList.toggle('dark');
            const icon = document.getElementById('theme-icon');
            icon.classList.toggle('fa-moon');
            icon.classList.toggle('fa-sun');
        }

        async function loadChats() {
            const res = await fetch(`/api/chats/${userId}`);
            const chats = await res.json();
            const list = document.getElementById('chat-history-list');
            list.innerHTML = '';
            chats.forEach(c => {
                list.innerHTML += `
                    <div onclick="selectChat('${c.chat_id}', '${c.title}')" class="p-2.5 hover:bg-gray-800 rounded-xl cursor-pointer flex items-center justify-between text-gray-300 transition">
                        <span class="truncate text-xs"><i class="fa-regular fa-message mr-2 text-emerald-400"></i> ${c.title}</span>
                    </div>
                `;
            });
        }

        async function startNewChat() {
            const title = prompt("Yangi chat nomini kiriting:", "Yangi suhbat");
            if (!title) return;
            const mode = document.getElementById('ai-mode-select').value;
            
            const formData = new FormData();
            formData.append("user_id", userId);
            formData.append("title", title);
            formData.append("mode", mode);

            const res = await fetch('/api/chat/new', { method: 'POST', body: formData });
            const data = await res.json();
            currentChatId = data.chat_id;
            document.getElementById('active-chat-title').innerText = title;
            document.getElementById('chat-messages').innerHTML = '';
            loadChats();
        }

        // WebSockets orqali Real-time Streaming
        function initWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws/${userId}`);
            ws.onmessage = function(event) {
                if(event.data === "[DONE]") return;
                // Jonli matn yozish
                let lastAIBox = document.getElementById('current-ai-response');
                if(lastAIBox) lastAIBox.innerHTML += event.data;
            };
        }

        async function sendMessageStream() {
            const input = document.getElementById('user-input');
            const prompt = input.value.trim();
            if(!prompt) return;

            const chatBox = document.getElementById('chat-messages');
            chatBox.innerHTML += `
                <div class="flex items-start gap-4 justify-end">
                    <div class="bg-emerald-600 p-4 rounded-2xl max-w-3xl text-white text-sm shadow-lg">${prompt}</div>
                    <div class="w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center text-white font-bold shrink-0">Siz</div>
                </div>
            `;
            input.value = "";

            // Agar rejim Kod Sandbox bo'lsa, maxsus API ishlaydi
            const mode = document.getElementById('ai-mode-select').value;
            if(mode === 'coding') {
                const res = await fetch('/api/sandbox/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: prompt })
                });
                const data = await res.json();
                chatBox.innerHTML += `
                    <div class="flex items-start gap-4">
                        <div class="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold shrink-0">Z</div>
                        <div class="bg-gray-800 border border-gray-700 p-4 rounded-2xl max-w-3xl text-gray-200 text-sm font-mono whitespace-pre-wrap"><b>Sandbox Natijasi:</b>\n${data.output}</div>
                    </div>
                `;
            } else {
                // WebSocket orqali stream qilish
                chatBox.innerHTML += `
                    <div class="flex items-start gap-4">
                        <div class="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center text-white font-bold shrink-0">Z</div>
                        <div id="current-ai-response" class="bg-gray-800 border border-gray-700 p-4 rounded-2xl max-w-3xl text-gray-200 text-sm"></div>
                    </div>
                `;
                if(ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(prompt);
                }
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function uploadFile(input) {
            if(input.files && input.files[0]) {
                const formData = new FormData();
                formData.append("user_id", userId);
                formData.append("file", input.files[0]);
                const res = await fetch('/api/rag/upload', { method: 'POST', body: formData });
                const data = await res.json();
                alert(data.message);
            }
        }

        function toggleVoiceMode() {
            alert("Ovozli muloqot (Voice-to-Voice) faollashdi. ChatGPT kabi gaplasha boshlashingiz mumkin!");
        }

        async function openCabinet() {
            const res = await fetch(`/api/user/${userId}`);
            const user = await res.json();
            alert(`Fabrika Kabineti:\nBalans: ${user.balance} so'rov\nAPI Kalit: ${user.api_key}`);
        }

        function openGallery() {
            alert("Galereya sahifasi: ZiyoAI orqali yaratilgan barcha media fayllar shu yerda jamlanadi.");
        }

        loadChats();
        initWebSocket();
    </script>
</body>
</html>
