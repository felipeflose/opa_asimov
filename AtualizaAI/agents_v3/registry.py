from typing import Dict, Type, Optional
from agents_v3.base import BaseAgent
from agents_v3.specialized import TelegramAgent, VisionAgent, FinOpsGuardian, SystemArchitectAgent
from core.gemini_client import GeminiClient

class AgentRegistry:
    """Registro mestre que mapeia identificadores de agentes para suas classes especialistas v3"""
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self._registry: Dict[str, Type[BaseAgent]] = {
            "TelegramAgent": TelegramAgent,
            "VisionAgent": VisionAgent,
            "FinOpsGuardian": FinOpsGuardian,
            "SystemArchitectAgent": SystemArchitectAgent
        }
        self._instances: Dict[str, BaseAgent] = {}

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Retorna uma instância (singleton) do agente solicitado"""
        if name not in self._registry:
            return None
            
        if name not in self._instances:
            agent_class = self._registry[name]
            self._instances[name] = agent_class(self.gemini_client)
            
        return self._instances[name]

    async def run_agent(self, name: str, task: str) -> str:
        """Executa um agente e retorna seu output"""
        agent = self.get_agent(name)
        if not agent:
            return f"Erro: Agente '{name}' não encontrado no registro v3."
            
        result = await agent.run(task)
        return result.output
