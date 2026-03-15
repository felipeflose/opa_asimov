import httpx
try:
    resp = httpx.get("https://flose-ai-platform-q2h7hqy4da-uc.a.run.app/telegram_webhook")
    print("GET Status:", resp.status_code)
    print("GET Body:", resp.text[:100])
except Exception as e:
    print("Error:", e)
