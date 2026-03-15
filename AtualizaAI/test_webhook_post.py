import httpx
import json

url = "https://flose-ai-platform-q2h7hqy4da-uc.a.run.app/telegram_webhook"
data = {
    "update_id": 12345,
    "message": {
        "message_id": 1,
        "from": {"id": 1, "first_name": "Test", "username": "testuser", "is_bot": False},
        "chat": {"id": 1, "type": "private"},
        "date": 1600000000,
        "text": "/start"
    }
}

try:
    resp = httpx.post(url, json=data)
    print("POST Status:", resp.status_code)
    print("POST Body:", resp.text)
except Exception as e:
    print("Error:", e)
