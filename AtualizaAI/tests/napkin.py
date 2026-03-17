import httpx
import asyncio
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("napkin-gemini")

load_dotenv()

class NapkinAI:
    def __init__(self):
        # Tokens via .env para segurança
        self.napkin_token = os.getenv("NAPKIN_API_KEY")
        self.gemini_token = os.getenv("GEMINI_API_KEY")
        
        if not self.napkin_token or not self.gemini_token:
            raise ValueError("❌ Faltam chaves de API no arquivo .env")

        # Configura Gemini
        genai.configure(api_key=self.gemini_token)
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')

        self.base_url = "https://api.napkin.ai/v1"

    async def _decide_visual_format(self, content: str) -> str:
        """Usa o Gemini para escolher o melhor visual_query do Napkin."""
        prompt = f"""
        Analise o texto abaixo e escolha o melhor formato de diagrama do Napkin.ai.
        Formatos aceitos: 'mindmap', 'flowchart', 'timeline', 'venn_diagram', 'swot_analysis', 'infographic'.

        Regras:
        1. Responda APENAS com a palavra do formato.
        2. Se houver sequência de passos, use 'flowchart'.
        3. Se houver datas, use 'timeline'.
        4. Se for um conceito central com ramificações, use 'mindmap'.
        
        Texto: "{content}"
        """
        try:
            response = self.gemini_model.generate_content(prompt)
            # Limpa a resposta para garantir que pegamos apenas a palavra-chave
            formato = response.text.strip().lower().replace("'", "").replace('"', '')
            logger.info(f"🤖 Gemini sugeriu o formato: {formato}")
            return formato
        except Exception as e:
            logger.warning(f"⚠️ Erro ao consultar Gemini, usando 'mindmap' como padrão. Erro: {e}")
            return "mindmap"

    async def generate(self, text: str, filename: str = "output.svg"):
        """Fluxo completo: Gemini decide -> Napkin cria -> Download."""
        
        # 1. Gemini decide o formato
        formato_escolhido = await self._decide_visual_format(text)

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Authorization": f"Bearer {self.napkin_token}", "Content-Type": "application/json"}
            
            # 2. Solicita ao Napkin
            payload = {
                "content": text,
                "visual_query": formato_escolhido,
                "format": "svg",
                "number_of_visuals": 1
            }
            
            logger.info(f"🚀 Solicitando {formato_escolhido} ao Napkin...")
            resp = await client.post(f"{self.base_url}/visual", json=payload, headers=headers)
            
            if resp.status_code not in [200, 201]:
                logger.error(f"❌ Erro Napkin: {resp.text}")
                return

            req_id = resp.json().get("id") or resp.json().get("request_id")

            # 3. Polling de Status
            download_url = None
            for _ in range(15):
                await asyncio.sleep(3)
                status_resp = await client.get(f"{self.base_url}/visual/{req_id}/status", headers=headers)
                data = status_resp.json()
                if data.get("status") == "completed":
                    download_url = data.get("generated_files", [{}])[0].get("url")
                    break
                logger.info(f"   Status: {data.get('status')}...")

            # 4. Download Final
            if download_url:
                img_resp = await client.get(download_url, headers={**headers, "Accept": "image/svg+xml"})
                with open(filename, "wb") as f:
                    f.write(img_resp.content)
                logger.info(f"✅ SUCESSO! Visual '{formato_escolhido}' salvo em: {filename}")

# --- Execução ---
async def main():
    ai = NapkinAI()
    
    # Teste com algo que sugira uma Timeline
    prompt_usuario = "Você é o especialista da Flose AI em ElevenLabs. Você sabe configurar vozes, clones de voz e integrar a API de TTS em sistemas multi-agente."
    
    await ai.generate(prompt_usuario, "computacao.svg")

if __name__ == "__main__":
    asyncio.run(main())