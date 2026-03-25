import os
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import structlog
from core.gemini_client import GeminiClient

logger = structlog.get_logger()

class AgentResult(BaseModel):
    output: str
    tokens_used: int
    cost_usd: float
    agent_name: str
    status: str = "success"

class BaseAgent:
    """Classe base v3 simplificada para todos os agentes especializados"""
    def __init__(self, name: str, purpose: str, system_prompt: str, gemini_client: GeminiClient):
        self.name = name
        self.purpose = purpose
        self.system_prompt = system_prompt
        self.gemini_client = gemini_client

    async def run(self, task: str, use_search: bool = True) -> AgentResult:
        """Executa a tarefa dada pelo orquestrador e retorna o resultado formatado"""
        try:
            logger.info("agent_run", agent=self.name, task=task[:50])
            
            # Executa prompt com FERRAMENTAS DE BUSCA ATIVADAS
            resp = await self.gemini_client.generate_text(
                prompt=task, 
                system_instruction=self.system_prompt,
                use_search=use_search
            )
            
            return AgentResult(
                output=resp.text,
                tokens_used=resp.tokens_in + resp.tokens_out,
                cost_usd=resp.cost_usd,
                agent_name=self.name
            )
        except Exception as e:
            logger.error("agent_error", agent=self.name, error=str(e))
            return AgentResult(
                output=f"Erro na execução do agente {self.name}: {str(e)}",
                tokens_used=0,
                cost_usd=0.0,
                agent_name=self.name,
                status="failed"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Converte o agente para representação no JSON registry"""
        return {
            "name": self.name,
            "purpose": self.purpose,
            "system_prompt": self.system_prompt,
            "agent_type": self.__class__.__name__
        }
