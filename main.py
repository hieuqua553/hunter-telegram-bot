from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openrouter/hunter-alpha"

@app.route("/", methods=["GET"])
def home():
    return "Hunter Alpha Telegram Bot đang chạy!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")
        
        # Gọi Hunter Alpha với system prompt chuyên automation
        ai_reply = get_hunter_response(user_text)
        
        # Gửi reply về Telegram
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
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    try:
        return resp.json()["choices"][0]["message"]["content"]
    except:
        return "Lỗi kết nối Hunter Alpha, thử lại sau nhé!"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
