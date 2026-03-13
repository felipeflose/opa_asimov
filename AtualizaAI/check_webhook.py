import os
import httpx
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
url = f"https://api.telegram.org/bot{token}/getWebhookInfo"

resp = httpx.get(url)
print("Webhook Info:", resp.json())
