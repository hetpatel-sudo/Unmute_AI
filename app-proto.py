import os
import json
import urllib.request
import urllib.error
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Safe shared placeholder. Replace locally or set GROQ_API_KEY.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "API_HERE")

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Current Groq multimodal model for camera image recognition.
VISION_MODEL = "qwen/qwen3.6-27b"


def get_groq_response(prompt, image_base64=None, model_name=DEFAULT_MODEL):
    if (
        not GROQ_API_KEY
        or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE"
    ):
        return (
            "⚠️ Groq API Key Missing: "
            "Replace YOUR_GROQ_API_KEY_HERE locally "
            "or set the GROQ_API_KEY environment variable."
        )

    url = "https://api.groq.com/openai/v1/chat/completions"

    if image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]

        system_prompt = """You are Unmuter, the Project Unmute accessibility assistant.

Analyze the actual webcam image for the Chapter 1 gesture set.

Supported labels and meanings:
HELP = I need help
HURT = I am hurt
WATER = I need water
FOOD = I need food
EMERGENCY = This is an emergency
DANGER = Danger ahead
STOP = Stop
BATHROOM = Where is the bathroom?
GOOD = Good
BAD = Bad

Return:
Label: <one supported label or UNKNOWN>
Phrase: <mapped phrase or UNKNOWN>
Confidence: <low, medium, or high>
Reason: <short explanation>

Important:
- Actually inspect the image.
- Do not pretend a gesture is visible when it is not.
- If the image is unclear, return UNKNOWN.
- This is a prototype, not a complete sign-language translator.
"""

        content = [
            {
                "type": "text",
                "text": prompt
                or "Recognize the Project Unmute Chapter 1 gesture."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url":
                        "data:image/jpeg;base64,"
                        + image_base64
                }
            }
        ]

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": content
            }
        ]

        request_model = VISION_MODEL

    else:
        messages = [
            {
                "role": "system",
                "content":
                    "You are Unmuter, a helpful, "
                    "ultra-fast, and intelligent AI assistant."
            },
            {
                "role": "user",
                "content": prompt or "Hello!"
            }
        ]

        request_model = model_name

    payload = {
        "model": request_model,
        "messages": messages,
        "temperature": 0.3 if image_base64 else 0.7,
        "max_tokens": 1024
    }

    data = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
    }

    req = urllib.request.Request(
        url,
        data=data,
        headers=headers
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=60
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

            return result["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as e:
        error_body = (
            e.read().decode("utf-8")
            if e.fp
            else ""
        )

        if e.code == 401:
            return (
                "⚠️ Groq API Error (401 Unauthorized): "
                "Invalid Groq API key."
            )

        return (
            f"⚠️ Groq API Error ({e.code}): "
            f"{error_body if error_body else e.reason}"
        )

    except Exception as e:
        return f"⚠️ System Error: {str(e)}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Unmuter AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Google Sans', sans-serif; }
        body { display: flex; height: 100vh; background-color: #f0f4f9; color: #1f1f1f; overflow: hidden; }
        
        .sidebar { width: 260px; background-color: #f0f4f9; display: flex; flex-direction: column; padding: 16px; justify-content: space-between; border-right: 1px solid #e3e3e3; }
        .sidebar-top { display: flex; flex-direction: column; gap: 16px; }
        .logo-container { display: flex; align-items: center; justify-content: space-between; padding: 4px 8px; }
        .logo { display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 18px; color: #0b57d0; }
        .btn-new-chat { display: flex; align-items: center; gap: 12px; background-color: #e6eef9; border: none; padding: 12px 16px; border-radius: 24px; font-weight: 500; color: #041e49; cursor: pointer; width: 100%; font-size: 14px; }
        .btn-new-chat:hover { background-color: #d3e3fd; }
        .nav-list { display: flex; flex-direction: column; gap: 2px; list-style: none; margin-top: 4px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 20px; color: #444746; cursor: pointer; font-size: 14px; }
        .nav-item:hover { background-color: #e3e3e3; }
        .section-title { font-size: 12px; color: #747775; margin: 12px 12px 4px; font-weight: 500; }
        .recents-list { display: flex; flex-direction: column; gap: 2px; list-style: none; overflow-y: auto; max-height: 160px; }
        .recent-item { padding: 8px 12px; border-radius: 16px; font-size: 13px; color: #444746; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
        .recent-item:hover { background-color: #e3e3e3; }
        .recent-item.active { background-color: #c2e7ff; color: #001d35; font-weight: 500; }
        
        .profile-section { display: flex; align-items: center; justify-content: space-between; padding: 8px; border-top: 1px solid #e3e3e3; }
        .profile-info { display: flex; align-items: center; gap: 10px; }
        .avatar { width: 32px; height: 32px; background-color: #0b57d0; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; }
        .profile-name { font-size: 14px; font-weight: 500; }
        
        .main-content { flex: 1; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 20px; background: radial-gradient(circle at 50% 30%, #ffffff 0%, #e8f0fe 70%, #f0f4f9 100%); position: relative; }
        .top-bar { width: 100%; display: flex; justify-content: flex-end; align-items: center; gap: 12px; }
        .btn-upgrade { background-color: #d3e3fd; color: #041e49; border: none; padding: 8px 20px; border-radius: 20px; font-weight: 500; display: flex; align-items: center; gap: 6px; cursor: pointer; font-size: 14px; }

        .chat-container { width: 100%; max-width: 820px; display: flex; flex-direction: column; align-items: center; margin: auto 0; }
        .greeting { font-size: 32px; font-weight: 500; color: #1f1f1f; margin-bottom: 20px; text-align: center; }
        
        .response-box { width: 100%; max-height: 380px; overflow-y: auto; margin-bottom: 20px; display: flex; flex-direction: column; gap: 12px; padding: 10px; }
        .msg { padding: 12px 18px; border-radius: 18px; max-width: 85%; font-size: 15px; line-height: 1.5; white-space: pre-wrap; }
        .user-msg { background-color: #e3e3e3; align-self: flex-end; border-bottom-right-radius: 4px; }
        .ai-msg { background-color: #ffffff; align-self: flex-start; border-bottom-left-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }

        .input-card { width: 100%; max-width: 780px; background: #ffffff; border-radius: 30px; padding: 8px 16px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); border: 1px solid #e0e0e0; }
        .btn-icon { background: none; border: none; color: #444746; cursor: pointer; padding: 8px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
        .btn-icon:hover { background-color: #f1f3f4; }
        .btn-icon.active-tts { color: #0b57d0; background-color: #e8f0fe; }
        .chat-input { flex: 1; border: none; outline: none; font-size: 16px; color: #1f1f1f; background: transparent; }
        
        .model-select-dropdown { border: none; background: #f0f4f9; font-size: 13px; color: #041e49; cursor: pointer; outline: none; font-weight: 500; padding: 6px 12px; border-radius: 16px; }

        .cam-modal { display: none; position: absolute; top: 10%; width: 420px; background: #ffffff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); padding: 16px; flex-direction: column; align-items: center; gap: 12px; z-index: 100; border: 1px solid #ccc; }
        .cam-modal video { width: 100%; height: 260px; border-radius: 12px; background: #000; object-fit: cover; }
        .cam-controls { display: flex; gap: 10px; width: 100%; }
        .cam-btn { flex: 1; padding: 10px; border: none; border-radius: 10px; cursor: pointer; font-weight: 500; }
        .cam-btn-capture { background: #0b57d0; color: white; }
        .cam-btn-close { background: #e3e3e3; color: #333; }
        
        .active-mic { color: #d93025; animation: pulse 1s infinite alternate; }
        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.2); } }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-top">
            <div class="logo-container">
                <div class="logo">
                    <span class="material-symbols-outlined" style="color:#0b57d0">graphic_eq</span>
                    Unmuter
                </div>
                <span class="material-symbols-outlined" style="color:#444746; cursor:pointer">view_sidebar</span>
            </div>
            <button class="btn-new-chat" onclick="initNewChat()">
                <span class="material-symbols-outlined">edit_square</span>
                New chat
            </button>
            <ul class="nav-list">
                <li class="nav-item"><span class="material-symbols-outlined">search</span> Search chats</li>
                <li class="nav-item"><span class="material-symbols-outlined">image</span> Images</li>
                <li class="nav-item"><span class="material-symbols-outlined">videocam</span> Videos</li>
                <li class="nav-item"><span class="material-symbols-outlined">grid_view</span> Library</li>
            </ul>

            <div class="section-title">Notebooks</div>
            <ul class="nav-list">
                <li class="nav-item"><span class="material-symbols-outlined">add</span> New notebook</li>
                <li class="nav-item"><span class="material-symbols-outlined">laptop</span> Multi-System Cluster</li>
            </ul>

            <div class="section-title">Recents</div>
            <ul class="recents-list" id="recentsList"></ul>
        </div>

        <div class="profile-section">
            <div class="profile-info">
                <div class="avatar">U</div>
                <div class="profile-name">USER</div>
            </div>
            <span class="material-symbols-outlined" style="color:#444746; cursor:pointer">settings</span>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <button class="btn-upgrade">
                <span class="material-symbols-outlined" style="font-size:18px">sparkles</span>
                Upgrade
            </button>
            <span class="material-symbols-outlined" style="color:#444746; cursor:pointer">draw</span>
        </div>

        <div class="cam-modal" id="camModal">
            <div style="font-weight:500; font-size:14px; width:100%; text-align:left;">Live Camera Feed</div>
            <video id="webcam" autoplay playsinline></video>
            <div class="cam-controls">
                <button class="cam-btn cam-btn-capture" onclick="captureCamera()">Capture & Send</button>
                <button class="cam-btn cam-btn-close" onclick="closeCamera()">Close</button>
            </div>
        </div>

        <div class="chat-container">
            <div class="greeting" id="greetingText">Unmute, USER</div>
            
            <div class="response-box" id="responseBox"></div>

            <div class="input-card">
                <button class="btn-icon" title="Open Camera Snapshot" onclick="openCamera()">
                    <span class="material-symbols-outlined">add</span>
                </button>
                
                <input type="text" class="chat-input" id="userInput" placeholder="Ask Unmuter..." onkeypress="handleKeyPress(event)">
                
                <select id="modelSelect" class="model-select-dropdown" title="Select Model Engine">
                    <option value="llama-3.3-70b-versatile" selected>Llama 3.3 70B</option>
                    <option value="llama-3.1-8b-instant">Llama 3.1 8B</option>
                    <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                </select>

                <button class="btn-icon" id="ttsBtn" title="Toggle Text-To-Speech" onclick="toggleTTS()">
                    <span class="material-symbols-outlined" id="ttsIcon">volume_off</span>
                </button>

                <button class="btn-icon" id="micBtn" title="Microphone Input" onclick="toggleMic()">
                    <span class="material-symbols-outlined">mic</span>
                </button>
            </div>
        </div>

        <div style="font-size:12px; color:#747775; margin-bottom: 8px;">
            Unmuter powered by Groq LPU speed. Double-check important facts.
        </div>
    </div>

    <script>
        let videoStream = null;
        let recognition = null;
        let ttsEnabled = false;
        let chatHistory = [];
        let activeChatId = null;

        // NEW: two-click microphone state
        let micRecording = false;
        let micTranscript = "";

        window.onload = function() {
            initNewChat();
        };

        function toggleTTS() {
            ttsEnabled = !ttsEnabled;
            const btn = document.getElementById('ttsBtn');
            const icon = document.getElementById('ttsIcon');

            if (ttsEnabled) {
                icon.innerText = 'volume_up';
                btn.classList.add('active-tts');
            } else {
                icon.innerText = 'volume_off';
                btn.classList.remove('active-tts');

                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }
            }
        }

        function initNewChat() {
            activeChatId = Date.now();
            document.getElementById('responseBox').innerHTML = '';
            document.getElementById('userInput').value = '';
            document.getElementById('greetingText').style.display = 'block';
            renderRecents();
        }

        function renderRecents() {
            const list = document.getElementById('recentsList');
            list.innerHTML = '';

            chatHistory.forEach(chat => {
                const li = document.createElement('li');
                li.className =
                    'recent-item' +
                    (chat.id === activeChatId ? ' active' : '');

                li.innerText = chat.title;
                li.onclick = () => loadChat(chat.id);
                list.appendChild(li);
            });
        }

        function loadChat(id) {
            activeChatId = id;

            const chat = chatHistory.find(c => c.id === id);
            const box = document.getElementById('responseBox');

            box.innerHTML = '';

            if (chat && chat.messages.length > 0) {
                document.getElementById('greetingText').style.display = 'none';

                chat.messages.forEach(m => {
                    appendMessageToDOM(m.sender, m.text);
                });
            } else {
                document.getElementById('greetingText').style.display = 'block';
            }

            renderRecents();
        }

        function appendMessage(sender, text) {
            document.getElementById('greetingText').style.display = 'none';
            appendMessageToDOM(sender, text);

            let chat = chatHistory.find(c => c.id === activeChatId);

            if (!chat) {
                const titleText =
                    text.length > 24
                        ? text.substring(0, 24) + '...'
                        : text;

                chat = {
                    id: activeChatId,
                    title: titleText,
                    messages: []
                };

                chatHistory.unshift(chat);

            } else if (chat.messages.length === 0) {
                chat.title =
                    text.length > 24
                        ? text.substring(0, 24) + '...'
                        : text;
            }

            chat.messages.push({
                sender,
                text
            });

            renderRecents();
        }

        function appendMessageToDOM(sender, text) {
            const box = document.getElementById('responseBox');

            const msg = document.createElement('div');
            msg.className =
                'msg ' + (sender === 'user' ? 'user-msg' : 'ai-msg');

            msg.innerText = text;

            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }


        // ====================================================
        // NEW MICROPHONE:
        // Click 1 = start recording
        // Click 2 = stop recording
        // Stop = automatically submit
        // ====================================================

        if (
            'webkitSpeechRecognition' in window ||
            'SpeechRecognition' in window
        ) {
            const SpeechRecognition =
                window.SpeechRecognition ||
                window.webkitSpeechRecognition;

            recognition = new SpeechRecognition();

            recognition.continuous = true;
            recognition.interimResults = false;
            recognition.lang = 'en-IN';

            recognition.onstart = function() {
                document.getElementById('micBtn')
                    .classList.add('active-mic');
            };

            recognition.onresult = function(e) {
                for (
                    let i = e.resultIndex;
                    i < e.results.length;
                    i++
                ) {
                    if (e.results[i].isFinal) {
                        const text =
                            e.results[i][0].transcript.trim();

                        if (text) {
                            micTranscript +=
                                (micTranscript ? ' ' : '') + text;
                        }
                    }
                }
            };

            recognition.onerror = function(e) {
                console.log(
                    'Speech recognition error:',
                    e.error
                );

                micRecording = false;
                micTranscript = "";

                document.getElementById('micBtn')
                    .classList.remove('active-mic');
            };

            recognition.onend = function() {
                document.getElementById('micBtn')
                    .classList.remove('active-mic');

                if (!micRecording && micTranscript.trim()) {
                    const finalText =
                        micTranscript.trim();

                    micTranscript = "";

                    document.getElementById('userInput').value =
                        finalText;

                    sendMessage();
                }
            };
        }


        function toggleMic() {
            if (!recognition) {
                alert(
                    'Speech recognition not supported on this browser.'
                );
                return;
            }

            // CLICK 1
            if (!micRecording) {
                micTranscript = "";
                micRecording = true;

                try {
                    recognition.start();
                } catch (err) {
                    console.log(err);
                    micRecording = false;
                }

                return;
            }

            // CLICK 2
            micRecording = false;

            try {
                recognition.stop();
            } catch (err) {
                console.log(err);
            }
        }


        // ====================================================
        // CAMERA
        // The old GUI is unchanged.
        // The captured image is now actually sent to the
        // backend as base64 image data.
        // ====================================================

        async function openCamera() {
            const modal =
                document.getElementById('camModal');

            const video =
                document.getElementById('webcam');

            modal.style.display = 'flex';

            try {
                videoStream =
                    await navigator.mediaDevices.getUserMedia({
                        video: true
                    });

                video.srcObject = videoStream;

            } catch (err) {
                alert(
                    'Camera access failed: ' + err.message
                );

                closeCamera();
            }
        }


        function closeCamera() {
            if (videoStream) {
                videoStream
                    .getTracks()
                    .forEach(track => track.stop());

                videoStream = null;
            }

            document.getElementById('camModal')
                .style.display = 'none';
        }


        function captureCamera() {
            const video =
                document.getElementById('webcam');

            const canvas =
                document.createElement('canvas');

            canvas.width =
                video.videoWidth || 640;

            canvas.height =
                video.videoHeight || 480;

            canvas
                .getContext('2d')
                .drawImage(
                    video,
                    0,
                    0,
                    canvas.width,
                    canvas.height
                );

            const imageBase64 =
                canvas.toDataURL(
                    'image/jpeg',
                    0.80
                );

            closeCamera();

            appendMessage(
                'user',
                '[Camera Snapshot Attached]'
            );

            sendBackendRequest({
                prompt:
                    'Recognize the Project Unmute Chapter 1 gesture in this camera snapshot.',
                image: imageBase64
            });
        }


        function handleKeyPress(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        }


        function sendMessage() {
            const input =
                document.getElementById('userInput');

            const text =
                input.value.trim();

            if (!text) return;

            appendMessage('user', text);

            input.value = '';

            sendBackendRequest({
                prompt: text
            });
        }


        async function sendBackendRequest(payload) {
            payload.model =
                document.getElementById(
                    'modelSelect'
                ).value;

            appendMessageToDOM(
                'ai',
                'Thinking (Groq LPU)...'
            );

            const box =
                document.getElementById(
                    'responseBox'
                );

            const loadingMsg =
                box.lastChild;

            try {
                const res =
                    await fetch(
                        '/api/query',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type':
                                    'application/json'
                            },
                            body:
                                JSON.stringify(payload)
                        }
                    );

                const data =
                    await res.json();

                loadingMsg.innerText =
                    data.response;

                let chat =
                    chatHistory.find(
                        c => c.id === activeChatId
                    );

                if (chat) {
                    chat.messages.push({
                        sender: 'ai',
                        text: data.response
                    });
                }

                if (ttsEnabled) {
                    speakText(data.response);
                }

            } catch (err) {
                loadingMsg.innerText =
                    'Error connecting to server.';
            }
        }


        function speakText(text) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();

                window.speechSynthesis.speak(
                    new SpeechSynthesisUtterance(text)
                );
            }
        }
    </script>
</body>
</html>"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/query", methods=["POST"])
def query():
    data = request.json or {}

    response = get_groq_response(
        data.get("prompt", ""),
        data.get("image"),
        data.get("model", DEFAULT_MODEL)
    )

    return jsonify({
        "status": "success",
        "response": response
    })


if __name__ == "__main__":
    print("====================================================")
    print(" Unmuter Web Application Running!")
    print(" Open Google Chrome: http://127.0.0.1:5000")
    print("====================================================")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
