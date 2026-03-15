from flask import Flask, request
import requests
import os
import json
import threading
import time

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/hunter-alpha"

def send_chat_action(chat_id, action="typing"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendChatAction"
    payload = {"chat_id": chat_id, "action": action}
    requests.post(url, json=payload)  # Không cần check response, fail cũng ok

def typing_loop(chat_id, stop_event):
    """Loop gửi typing mỗi 4 giây cho đến khi stop_event được set"""
    while not stop_event.is_set():
        send_chat_action(chat_id, "typing")
        time.sleep(4)  # <5s để an toàn, tránh flood

@app.route("/", methods=["GET"])
def home():
    return "Hunter Alpha Telegram Bot đang chạy!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")
        
        # Bắt đầu hiệu ứng typing loop (chạy nền)
        stop_event = threading.Event()
        typing_thread = threading.Thread(target=typing_loop, args=(chat_id, stop_event))
        typing_thread.daemon = True
        typing_thread.start()
        
        # Gọi Hunter Alpha
        ai_reply = get_hunter_response(user_text)
        
        # Dừng typing loop
        stop_event.set()
        typing_thread.join(timeout=1)  # Đợi luồng dừng
        
        # Gửi reply về Telegram (typing tự tắt khi gửi message)
        send_telegram_message(chat_id, ai_reply)
    
    return "OK", 200

def get_hunter_response(user_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://railway.app"  # optional
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Bạn là Hunter Alpha - AI Agent chuyên tự động hoá. Hãy suy nghĩ step-by-step, lập kế hoạch chi tiết, đưa ra hành động cụ thể, và hỗ trợ user thực hiện task automation (lập kế hoạch, nhắc nhở, phân tích, workflow...). Trả lời bằng tiếng Việt, ngắn gọn nhưng đầy đủ."
            },
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Lỗi kết nối Hunter Alpha: {str(e)}. Thử lại sau nhé!"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
