import os
from typing import Dict, Type, Optional, List
from agents_v3.base import BaseAgent
from agents_v3.specialized import TelegramAgent, VisionAgent, FinOpsGuardian, SystemArchitectAgent
from core.gemini_client import GeminiClient
from storage_v3.gcs import GCSClient
import structlog

logger = structlog.get_logger()

class AgentRegistry:
    """Registro mestre que gerencia agentes especialistas e dinâmicos v3"""
    def __init__(self, gemini_client: GeminiClient, project_id: str):
        self.gemini_client = gemini_client
        self.project_id = project_id
        self.bucket = f"flose-ai-platform-{project_id}"
        self.gcs = GCSClient(self.bucket)
        
        # Agentes com lógica de código especializada
        self._specialized_classes: Dict[str, Type[BaseAgent]] = {
            "TelegramAgent": TelegramAgent,
            "VisionAgent": VisionAgent,
            "FinOpsGuardian": FinOpsGuardian,
            "SystemArchitectAgent": SystemArchitectAgent
        }
        self._instances: Dict[str, BaseAgent] = {}

    async def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Retorna uma instância do agente solicitado (especialista ou dinâmico)"""
        # 1. Verifica cache de instâncias
        if name in self._instances:
            return self._instances[name]
            
        # 2. Verifica se é um agente especialista codificado
        if name in self._specialized_classes:
            agent_class = self._specialized_classes[name]
            # Tenta carregar config do GCS mesmo para especialistas (override de tools/prompt)
            dynamic_config = await self._load_dynamic_config(name)
            
            instance = agent_class(self.gemini_client)
            if dynamic_config:
                instance.tools = dynamic_config.get("tools", [])
                instance.system_prompt = dynamic_config.get("system_prompt", instance.system_prompt)
                instance.rag = dynamic_config.get("rag", instance.rag)
                
            self._instances[name] = instance
            return instance

        # 3. Busca no registro dinâmico do GCS
        config = await self._load_dynamic_config(name)
        if config:
            instance = BaseAgent(
                name=config["name"],
                purpose=config["purpose"],
                system_prompt=config["system_prompt"],
                gemini_client=self.gemini_client,
                tools=config.get("tools", []),
                rag=config.get("rag", {"files": [], "links": []})
            )
            self._instances[name] = instance
            return instance
            
        return None

    async def _load_dynamic_config(self, name: str) -> Optional[dict]:
        """Carrega a configuração de um agente específico do registro JSON no GCS"""
        try:
            data = self.gcs.get_json("agents/registry_v3.json")
            if not data or "agents" not in data:
                return None
            
            for agent_data in data["agents"]:
                if agent_data["name"] == name:
                    return agent_data
            return None
        except Exception as e:
            logger.error("registry_load_error", agent=name, error=str(e))
            return None

    async def run_agent(self, name: str, task: str) -> str:
        """Executa um agente e retorna seu output"""
        agent = await self.get_agent(name)
        if not agent:
            return f"Erro: Agente '{name}' não encontrado no registro v3 (GCS ou Local)."
            
        result = await agent.run(task)
        return result.output
