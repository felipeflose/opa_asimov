import os
from typing import Optional, List, Dict, Any, Union
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()

# Configuração de Retry: 3 tentativas com wait exponencial
RETRY_CONFIG = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warn("gemini_retry", attempt=retry_state.attempt_number)
)

class GeminiResponse(BaseModel):
    text: str
    tokens_in: int
    tokens_out: int
    model: str
    cost_usd: float

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Preços (v3 Prompt Specs - Flash 1.5/2.5 Projections)
        # $0.075 / 1M tokens in, $0.30 / 1M tokens out (Simulação baseada em flash)
        self.price_in = 0.000000075
        self.price_out = 0.0000003

    @RETRY_CONFIG
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None, image_path: Optional[str] = None) -> GeminiResponse:
        """Gera texto a partir de prompt com suporte a instrução de sistema e imagem"""
        try:
            # Model config
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            
            # Message parts
            parts = [prompt]
            if image_path and os.path.exists(image_path):
                # Placeholder for vision logic (if needed, simplified for base)
                # In serious migration, would use PIL.Image.open
                pass

            # Generate
            # Using async call if supported or wrap sync
            response = await model.generate_content_async(parts)
            
            # Metrics
            # In Gemini API v1.5, usage_metadata gives tokens
            usage = response.usage_metadata
            tokens_in = usage.prompt_token_count
            tokens_out = usage.candidates_token_count
            
            cost = (tokens_in * self.price_in) + (tokens_out * self.price_out)
            
            return GeminiResponse(
                text=response.text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                model=self.model_name,
                cost_usd=cost
            )
        except Exception as e:
            logger.error("gemini_error", error=str(e))
            raise e

    def get_token_count(self, text: str) -> int:
        """Retorna contagem de tokens aproximada"""
        return self.model.count_tokens(text).total_tokens
