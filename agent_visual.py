import os
import requests
import logging
import asyncio

logger = logging.getLogger(__name__)

class VisualAgent:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        self.base_url = "https://api.napkin.ai/v1/visual"

    async def create_diagram(self, update, context, content):
        if not self.token: return
        try:
            payload = {"format": "png", "content": content, "number_of_visuals": 1}
            resp = requests.post(self.base_url, json=payload, headers=self.headers, timeout=30)
            if resp.status_code not in [200, 201]: return
            
            req_id = resp.json().get("id")
            for i in range(25):
                await asyncio.sleep(5)
                status_resp = requests.get(f"{self.base_url}/{req_id}/status", headers=self.headers)
                if status_resp.status_code != 200: continue
                data = status_resp.json()
                if data.get("status") == "completed":
                    files = data.get("generated_files", [])
                    if files:
                        img_resp = requests.get(files[0].get("url"), headers=self.headers)
                        if img_resp.status_code == 200:
                            path = f"napkin_{req_id}.png"
                            with open(path, "wb") as f:
                                f.write(img_resp.content)
                            try:
                                with open(path, 'rb') as f:
                                    await context.bot.send_photo(chat_id=update.message.chat_id, photo=f, caption="\u2728 Visual gerado pelo VisualAgent")
                            finally:
                                if os.path.exists(path):
                                    os.remove(path)
                            return
                elif data.get("status") == "failed": return
        except Exception as e:
            logger.error(f"VisualAgent: {e}")
