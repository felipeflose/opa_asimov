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

from services.scraper import WebScraper

class BaseAgent:
    """Classe base v3 simplificada para todos os agentes especializados"""
    def __init__(self, name: str, purpose: str, system_prompt: str, gemini_client: GeminiClient, tools: List[str] = None, rag: Dict = None):
        self.name = name
        self.purpose = purpose
        self.system_prompt = system_prompt
        self.gemini_client = gemini_client
        self.tools = tools or []
        self.rag = rag or {"files": [], "links": []}

    async def run(self, task: str) -> AgentResult:
        """Executa a tarefa dada pelo orquestrador e retorna o resultado formatado"""
        try:
            logger.info("agent_run", agent=self.name, task=task[:50])
            
            # 1. Coleta conhecimento externo (RAG Links)
            external_context = ""
            links = self.rag.get("links", [])
            if links:
                logger.info("rag_link_browsing", agent=self.name, count=len(links))
                for link in links:
                    content = await WebScraper.get_content(link)
                    if content:
                        external_context += f"\n--- CONTEÚDO DO LINK ({link}) ---\n{content}\n"

            # 2. Prepara o prompt Final com Conhecimento Injetado
            final_task = task
            if external_context:
                final_task = (
                    "USE O CONHECIMENTO EXTERNO ABAIXO PARA RESPONDER À TAREFA SE RELEVANTE:\n\n"
                    f"{external_context}\n\n"
                    "--------------------------------------------------\n"
                    f"TAREFA DO USUÁRIO: {task}"
                )

            # 3. Executa prompt com FERRAMENTAS DINÂMICAS do registro
            use_search = "google_search" in self.tools
            
            resp = await self.gemini_client.generate_text(
                prompt=final_task, 
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
            "tools": self.tools,
            "rag": self.rag,
            "agent_type": self.__class__.__name__
        }
