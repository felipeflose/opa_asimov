import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/getWebhookInfo"

resp = httpx.get(url)
info = resp.json()
print("Webhook Info Status:", info.get('ok'))
if 'result' in info:
    res = info['result']
    print(f"URL: {res.get('url')}")
    print(f"Last Error: {res.get('last_error_message')}")
    print(f"Pending Updates: {res.get('pending_update_count')}")
