import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.main import app

# Add CORS middleware dynamically so we don't modify your app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A rich, modern UI to test your agent
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHL Assessment Recommender UI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --chat-bg: #1e293b;
            --primary: #10b981;
            --primary-hover: #059669;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --user-msg: #3b82f6;
            --bot-msg: #334155;
            --card-bg: #0f172a;
            --border: #334155;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            display: flex;
            justify-content: center;
            height: 100vh;
        }

        .chat-container {
            width: 100%;
            max-width: 800px;
            background-color: var(--chat-bg);
            display: flex;
            flex-direction: column;
            height: 100vh;
            box-shadow: 0 0 20px rgba(0,0,0,0.5);
            border-left: 1px solid var(--border);
            border-right: 1px solid var(--border);
        }

        .chat-header {
            padding: 20px;
            border-bottom: 1px solid var(--border);
            text-align: center;
            background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        }

        .chat-header h1 {
            margin: 0;
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary);
        }
        
        .chat-header p {
            margin: 4px 0 0 0;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .chat-box {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 0.95rem;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            background-color: var(--user-msg);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .bot-message {
            background-color: var(--bot-msg);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }

        .recommendations-container {
            margin-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .rec-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .rec-title {
            font-weight: 600;
            color: var(--primary);
            text-decoration: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .rec-title:hover {
            text-decoration: underline;
        }

        .badge {
            background-color: var(--primary);
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }

        .input-area {
            padding: 20px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 10px;
            background-color: var(--chat-bg);
        }

        input[type="text"] {
            flex-grow: 1;
            padding: 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background-color: var(--card-bg);
            color: var(--text-main);
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus {
            border-color: var(--primary);
        }

        button {
            padding: 0 20px;
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        button:hover {
            background-color: var(--primary-hover);
        }
        
        button:disabled {
            background-color: var(--bot-msg);
            cursor: not-allowed;
        }

        .typing-indicator {
            align-self: flex-start;
            color: var(--text-muted);
            font-size: 0.85rem;
            display: none;
            padding: 0 16px;
        }
        
        .sys-msg {
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin: 10px 0;
        }
    </style>
</head>
<body>

<div class="chat-container">
    <div class="chat-header">
        <h1>SHL Assessment Recommender</h1>
        <p>Take-home Assignment Test UI</p>
    </div>
    
    <div class="chat-box" id="chatBox">
        <div class="message bot-message">
            Hi! I am the SHL Assessment Recommender. What role are you hiring for today?
        </div>
    </div>
    
    <div class="typing-indicator" id="typingIndicator">Agent is thinking...</div>

    <div class="input-area">
        <input type="text" id="userInput" placeholder="E.g., I am hiring a Java developer..." autocomplete="off">
        <button id="sendBtn" onclick="sendMessage()">Send</button>
    </div>
</div>

<script>
    // State to hold stateless history required by backend
    let conversationHistory = [];
    const chatBox = document.getElementById('chatBox');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');

    userInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    function appendMessage(role, text, recommendations = [], isEnd = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
        
        // Add text
        const textSpan = document.createElement('div');
        textSpan.textContent = text;
        msgDiv.appendChild(textSpan);

        // Add recommendations if any
        if (recommendations && recommendations.length > 0) {
            const recContainer = document.createElement('div');
            recContainer.className = 'recommendations-container';
            
            recommendations.forEach(rec => {
                const card = document.createElement('a');
                card.className = 'rec-card rec-title';
                card.href = rec.url;
                card.target = '_blank';
                
                card.innerHTML = `
                    <span>${rec.name}</span>
                    <span class="badge" title="Test Type">Type: ${rec.test_type}</span>
                `;
                recContainer.appendChild(card);
            });
            msgDiv.appendChild(recContainer);
        }

        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        
        if (isEnd) {
            const sysMsg = document.createElement('div');
            sysMsg.className = 'sys-msg';
            sysMsg.textContent = "Conversation Ended (end_of_conversation: true)";
            chatBox.appendChild(sysMsg);
            chatBox.scrollTop = chatBox.scrollHeight;
            userInput.disabled = true;
            sendBtn.disabled = true;
            userInput.placeholder = "Conversation ended.";
        }
    }

    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Display user msg
        appendMessage('user', text);
        userInput.value = '';
        
        // Update stateless history
        conversationHistory.push({ role: 'user', content: text });

        // Show typing
        typingIndicator.style.display = 'block';
        sendBtn.disabled = true;
        userInput.disabled = true;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: conversationHistory })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Add to history so it's passed on the next turn
            conversationHistory.push({ role: 'assistant', content: data.reply });

            appendMessage('assistant', data.reply, data.recommendations, data.end_of_conversation);
        } catch (error) {
            console.error("Error calling chat endpoint:", error);
            appendMessage('assistant', 'Sorry, there was an error communicating with the server.');
            // Pop the last user message so they can try again
            conversationHistory.pop();
        } finally {
            typingIndicator.style.display = 'none';
            sendBtn.disabled = false;
            userInput.disabled = false;
            userInput.focus();
        }
    }
</script>

</body>
</html>
"""

@app.get("/ui", response_class=HTMLResponse)
def get_ui():
    return HTML_CONTENT

if __name__ == "__main__":
    print("Starting temporary UI server...")
    print("Go to http://127.0.0.1:8000/ui in your browser")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
