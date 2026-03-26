import os
from typing import Optional, Dict, Any, List, Union
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

import hashlib
from services.scraper import WebScraper
from storage_v3.gcs import GCSClient

class BaseAgent:
    """Classe base v3 simplificada para todos os agentes especializados"""
    def __init__(self, name: str, purpose: str, system_prompt: str, gemini_client: GeminiClient, tools: List[str] = None, rag: Dict = None, gcs_client: Optional[GCSClient] = None, status: str = "ready", training_progress: int = 100):
        self.name = name
        self.purpose = purpose
        self.system_prompt = system_prompt
        self.gemini_client = gemini_client
        self.tools = tools or []
        self.rag = rag or {"files": [], "links": []}
        self.gcs = gcs_client
        self.status = status
        self.training_progress = training_progress

    async def run(self, task: str) -> AgentResult:
        """Executa a tarefa dada pelo orquestrador e retorna o resultado formatado"""
        if self.status == "in_training":
            return AgentResult(
                output=f"Lamento, o agente {self.name} ainda está na 'Sala de Aula' sendo treinado e não pode responder agora. Por favor, aguarde o treinamento atingir 100%!",
                tokens_used=0,
                cost_usd=0.0,
                agent_name=self.name,
                status="in_training"
            )
        
        try:
            logger.info("agent_run", agent=self.name, task=task[:50])
            
            # 1. Coleta conhecimento externo (RAG Links com Cache no GCS)
            external_context = ""
            links = self.rag.get("links", [])
            for link in links:
                content = None
                cache_path = None
                
                # Tenta ler do cache no GCS se disponível
                if self.gcs:
                    link_hash = hashlib.md5(link.encode()).hexdigest()
                    cache_path = f"agents/{self.name}/rag/cache/{link_hash}.txt"
                    try:
                        blob = self.gcs.bucket.blob(cache_path)
                        if blob.exists():
                            content = blob.download_as_text()
                            logger.info("rag_cache_hit", agent=self.name, link=link)
                    except Exception: pass
                
                # Se não tem cache, faz scraping e salva
                if not content:
                    logger.info("rag_link_scraping", agent=self.name, link=link)
                    content = await WebScraper.get_content(link)
                    if content and self.gcs and cache_path:
                        try:
                            self.gcs.bucket.blob(cache_path).upload_from_string(content)
                            logger.info("rag_cache_saved", agent=self.name, path=cache_path)
                        except Exception: pass
                
                if content:
                    external_context += f"\n--- CONTEÚDO DO LINK ({link}) ---\n{content}\n"

            # 2. Processa Documentos (Arquivos RAG)
            files = self.rag.get("files", [])
            for file_path in files:
                if self.gcs:
                    try:
                        blob = self.gcs.bucket.blob(file_path)
                        if blob.exists():
                            file_content = blob.download_as_text()
                            external_context += f"\n--- CONTEÚDO DO ARQUIVO ({file_path}) ---\n{file_content}\n"
                    except Exception: pass

            # 3. Prepara o prompt Final com Conhecimento Injetado
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
            "status": self.status,
            "training_progress": self.training_progress,
            "agent_type": self.__class__.__name__
        }
