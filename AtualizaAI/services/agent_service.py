from typing import List, Optional, Dict
from storage_v3.gcs import GCSClient
import structlog

logger = structlog.get_logger()

class AgentService:
    """Serviço de Domínio para gerenciar o registro de agentes no GCS"""
    def __init__(self, gcs: GCSClient):
        self.gcs = gcs
        self.registry_path = "agents/registry_v3.json"

    async def list_agents(self) -> List[Dict]:
        """Retorna todos os agentes registrados"""
        data = self.gcs.get_json(self.registry_path)
        if not data or "agents" not in data:
            return []
        return data["agents"]

    async def get_agent(self, name: str) -> Optional[Dict]:
        """Busca um agente pelo nome"""
        agents = await self.list_agents()
        return next((a for a in agents if a["name"] == name), None)

    async def save_agent(self, agent_data: Dict) -> bool:
        """Adiciona ou atualiza um agente no registro"""
        # Validação simples
        if not agent_data.get("name") or not agent_data.get("system_prompt"):
            raise ValueError("Nome e System Prompt são obrigatórios para o Agente.")

        registry = self.gcs.get_json(self.registry_path) or {"agents": []}
        
        # Upsert
        found = False
        for i, a in enumerate(registry["agents"]):
            if a["name"] == agent_data["name"]:
                registry["agents"][i] = agent_data
                found = True
                break
        
        if not found:
            registry["agents"].append(agent_data)
            
        return self.gcs.upload_json(registry, self.registry_path)

    async def delete_agent(self, name: str) -> bool:
        """Remove um agente do registro"""
        registry = self.gcs.get_json(self.registry_path)
        if not registry: return False
        
        new_agents = [a for a in registry["agents"] if a["name"] != name]
        if len(new_agents) == len(registry["agents"]):
            return False
            
        registry["agents"] = new_agents
        return self.gcs.upload_json(registry, self.registry_path)
