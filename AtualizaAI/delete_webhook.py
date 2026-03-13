import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")

# 1. Remove o Webhook
resp = httpx.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
print("deleteWebhook:", resp.json())

# 2. Confirma
info = httpx.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
print("getWebhookInfo:", info.json())
