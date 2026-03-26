import httpx
from bs4 import BeautifulSoup
import structlog
from typing import Optional

logger = structlog.get_logger()

class WebScraper:
    """Serviço simplificado para extração de conteúdo de URLs para o RAG v3"""
    
    @staticmethod
    async def get_content(url: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Remove scripts, styles e outros elementos indesejados
                for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
                    script_or_style.decompose()
                
                # Extrai texto limpo
                text = soup.get_text(separator=' ')
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                
                # Limite de segurança para não explodir os tokens (30k chars ~ 7k tokens)
                return clean_text[:30000]
                
        except Exception as e:
            logger.error("scraper_error", url=url, error=str(e))
            return None
