import httpx
import json
import logging
import asyncio
import os

logger = logging.getLogger("napkin-client")

class NapkinClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NAPKIN_API_KEY")
        self.base_url = "https://api.napkin.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def generate_visual(self, content: str, style_id: str = None, visual_query: str = "mindmap"):
        """
        Gera um visual baseado no texto fornecido.
        """
        payload = {
            "format": "png",
            "content": content,
            "visual_query": visual_query,
            "number_of_visuals": 1,
            "transparent_background": True
        }
        if style_id:
            payload["style_id"] = style_id

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/visual", json=payload, headers=self.headers, timeout=60)
                if response.status_code == 201:
                    return response.json()
                else:
                    logger.error(f"Napkin API Error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Napkin Client Exception: {e}")
                return None

    async def get_visual_status(self, visual_id: str):
        """
        Verifica o status e obtém o link do visual gerado.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/visual/{visual_id}", headers=self.headers, timeout=30)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Napkin API Status Error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Napkin Status Exception: {e}")
                return None
