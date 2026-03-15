import google.generativeai as genai
import json
import os
from datetime import datetime

class BaseAgent:
    def __init__(self, name, purpose, system_prompt=None, avatar=None, tools=None, gcs_client=None):
        self.name = name
        self.purpose = purpose
        self.system_prompt = system_prompt or f"Você é o {self.name}, um agente especializado em {self.purpose}."
        self.avatar = avatar or "https://api.dicebear.com/7.x/bottts/svg?seed=" + self.name
        self.tools = tools or []
        self.gcs_client = gcs_client
        self.memory_path = f"agents/memory/{self.name}/"
        
    def to_dict(self):
        # Tenta carregar métricas existentes se houver
        metrics = {"executions": 0, "total_tokens": 0}
        if self.gcs_client:
            agent_data = self.gcs_client.read_json(f"agents/{self.name}.json")
            if agent_data and "metrics" in agent_data:
                metrics = agent_data["metrics"]

        return {
            "agent_name": self.name,
            "purpose": self.purpose,
            "system_prompt": self.system_prompt,
            "avatar": self.avatar,
            "tools": self.tools,
            "memory": self.memory_path,
            "token_cost_profile": "standard",
            "metrics": metrics,
            "created_at": datetime.now().isoformat()
        }

    def save_to_registry(self):
        if self.gcs_client:
            self.gcs_client.upload_json(self.to_dict(), f"agents/{self.name}.json")
            # Also update registry.json
            registry = self.gcs_client.read_json("agents/registry.json") or {"agents": []}
            
            # Update or Append
            found = False
            for i, a in enumerate(registry['agents']):
                if a['agent_name'] == self.name:
                    registry['agents'][i] = self.to_dict()
                    found = True
                    break
            
            if not found:
                registry['agents'].append(self.to_dict())
                
            self.gcs_client.upload_json(registry, "agents/registry.json")

    def run(self, task):
        """Executa uma tarefa usando a inteligência e personalidade deste agente."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Erro: GEMINI_API_KEY não configurada."
            
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            {self.system_prompt}
            
            SUA TAREFA ATUAL:
            {task}
            
            Responda como o agente {self.name}. Forneça uma solução técnica, um relatório ou o resultado da execução.
            """
            response = model.generate_content(prompt)
            
            # Atualizar Métricas
            if self.gcs_client:
                agent_data = self.gcs_client.read_json(f"agents/{self.name}.json") or self.to_dict()
                if "metrics" not in agent_data: agent_data["metrics"] = {"executions": 0, "total_tokens": 0}
                agent_data["metrics"]["executions"] += 1
                if hasattr(response, 'usage_metadata'):
                    agent_data["metrics"]["total_tokens"] += response.usage_metadata.total_token_count
                
                self.gcs_client.upload_json(agent_data, f"agents/{self.name}.json")
                # Sincroniza registry
                registry = self.gcs_client.read_json("agents/registry.json")
                if registry:
                    for a in registry.get("agents", []):
                        if a["agent_name"] == self.name:
                            a["metrics"] = agent_data["metrics"]
                            break
                    self.gcs_client.upload_json(registry, "agents/registry.json")

            return response.text.strip()
        except Exception as e:
            return f"Erro na execução do agente {self.name}: {str(e)}"
