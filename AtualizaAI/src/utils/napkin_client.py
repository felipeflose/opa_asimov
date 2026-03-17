import httpx
import asyncio
import os
import logging
import google.generativeai as genai
from google.cloud import storage

logger = logging.getLogger("napkin-ai")

class NapkinClient:
    """
    Cliente integrado Gemini + Napkin AI.
    Gemini escolhe o melhor formato visual, Napkin gera o diagrama.
    """
    def __init__(self, api_key: str = None, gemini_key: str = None):
        self.napkin_token = api_key or os.getenv("NAPKIN_API_KEY")
        gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://api.napkin.ai/v1"
        
        if gemini_key:
            genai.configure(api_key=gemini_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            self.gemini = genai.GenerativeModel(model_name)
        else:
            self.gemini = None

    async def _decide_format(self, content: str) -> str:
        """Usa o Gemini para escolher o melhor formato visual."""
        if not self.gemini:
            return "mindmap"
        prompt = f"""
        Analise o texto e escolha o melhor formato de diagrama.
        Formatos válidos APENAS: mindmap, flowchart, timeline, venn_diagram, swot_analysis, infographic
        Responda APENAS com uma única palavra do formato acima.
        
        Texto: "{content[:500]}"
        """
        try:
            resp = self.gemini.generate_content(prompt)
            fmt = resp.text.strip().lower().replace("'", "").replace('"', '').split()[0]
            valid = ["mindmap", "flowchart", "timeline", "venn_diagram", "swot_analysis", "infographic"]
            return fmt if fmt in valid else "mindmap"
        except:
            return "mindmap"

    async def generate_and_return_url(self, content: str) -> str | None:
        """
        Fluxo completo: Gemini decide formato → Napkin gera → retorna URL do SVG.
        """
        if not self.napkin_token:
            logger.error("NAPKIN_API_KEY não configurada")
            return None

        formato = await self._decide_format(content)
        headers = {
            "Authorization": f"Bearer {self.napkin_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "content": content,
            "visual_query": formato,
            "format": "svg",
            "number_of_visuals": 1
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/visual", json=payload, headers=headers)
            if resp.status_code not in [200, 201]:
                logger.error(f"Napkin create error: {resp.status_code}")
                return None

            req_id = resp.json().get("id") or resp.json().get("request_id")
            if not req_id:
                return None

            for _ in range(15):
                await asyncio.sleep(3)
                status_resp = await client.get(
                    f"{self.base_url}/visual/{req_id}/status",
                    headers=headers
                )
                data = status_resp.json()
                status = data.get("status", "").lower()
                
                if status == "completed":
                    generated_files = data.get("generated_files") or data.get("files") or []
                    if len(generated_files) > 0:
                        url = generated_files[0].get("url")
                        logger.info(f"Napkin visual gerado ({formato}): {url}")
                        return url
                    return None
                
                if status in ["failed", "error", "rejected"]:
                    logger.error(f"Napkin falhou: {data}")
                    return None

        return None

    async def generate_and_upload_to_gcs(self, content: str, gcs_client, filename: str) -> str | None:
        """
        Gera o visual e faz upload para o GCS respeitando o namespace do usuário.
        Retorna a URL pública ou None se falhar.
        """
        url = await self.generate_and_return_url(content)
        if not url:
            return None

        # Baixa o SVG (diagrama)
        headers = {
            "Authorization": f"Bearer {self.napkin_token}",
            "Accept": "image/svg+xml"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to download Napkin SVG: {resp.status_code}")
                return url # fallback

            svg_bytes = resp.content

        # Faz upload para GCS usando o caminho completo (Namespace amigável)
        try:
            # Pasta dedicada para visuais
            gcs_path = f"visuals/marketplace/{filename}"
            full_remote_path = gcs_client._full_path(gcs_path)
            
            blob = gcs_client.bucket.blob(full_remote_path)
            blob.upload_from_string(svg_bytes, content_type="image/svg+xml")
            
            # Retorna URL pública persistente
            final_url = f"https://storage.googleapis.com/{gcs_client.bucket_name}/{full_remote_path}"
            logger.info(f"Visual persistido no GCS: {final_url}")
            return final_url
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            return url # fallback para URL original se falhar o upload