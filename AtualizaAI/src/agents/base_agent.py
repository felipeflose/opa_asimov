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
            # Ideia 6: Versionamento de Prompts
            version_id = datetime.now().strftime("%Y%m%d_%H%M")
            agent_snapshot = self.to_dict()
            agent_snapshot["version"] = version_id
            
            # 1. Salva snapshot histórico
            self.gcs_client.upload_json(agent_snapshot, f"agents/versions/{self.name}/{version_id}.json")
            
            # 2. Salva estado atual
            self.gcs_client.upload_json(agent_snapshot, f"agents/{self.name}.json")

            # 3. Sincroniza registry global
            registry = self.gcs_client.read_json("agents/registry.json") or {"agents": []}
            found = False
            for i, a in enumerate(registry['agents']):
                if a['agent_name'] == self.name:
                    registry['agents'][i] = agent_snapshot
                    found = True
                    break
            
            if not found:
                registry['agents'].append(agent_snapshot)
                
            self.gcs_client.upload_json(registry, "agents/registry.json")

    def run(self, task):
        """Executa uma tarefa usando a inteligência e personalidade deste agente."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Erro: GEMINI_API_KEY não configurada.", {}
            
        try:
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            prompt = f"""
            {self.system_prompt}
            
            SUA TAREFA ATUAL:
            {task}
            
            Responda como o agente {self.name}. Forneça uma solução técnica, um relatório ou o resultado da execução.
            ⚠️ REGRA CRÍTICA: Sua resposta deve ser DIRETA e CONCISA, com no máximo 4 frases. Use linguagem natural em português brasileiro.
            """
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # Auto-avaliação (Ideia 2)
            eval_prompt = f"""
            Tarefa executada: "{task[:300]}"
            Resultado produzido: "{result[:500]}"
            Responda APENAS com JSON válido:
            {{"confidence": 0.0_to_1.0, "quality": "high|medium|low", "learned": ["conceito1"], "improvement": "dica"}}
            """
            eval_resp = model.generate_content(eval_prompt)
            import re, json as _json
            raw = eval_resp.text.strip()
            
            # Limpeza de JSON robusta
            if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw: raw = raw.split("```")[1].split("```")[0].strip()
            
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            evaluation = _json.loads(match.group()) if match else {"confidence": 0.5, "quality": "medium"}

            # Atualizar Métricas e Performance no GCS
            if self.gcs_client:
                # 1. Métricas Acumuladas
                agent_data = self.gcs_client.read_json(f"agents/{self.name}.json") or self.to_dict()
                if "metrics" not in agent_data: agent_data["metrics"] = {"executions": 0, "total_tokens": 0}
                agent_data["metrics"]["executions"] += 1
                if hasattr(response, 'usage_metadata'):
                    agent_data["metrics"]["total_tokens"] += response.usage_metadata.total_token_count
                
                self.gcs_client.upload_json(agent_data, f"agents/{self.name}.json")
                
                # 2. Log de Performance Histórico
                perf_log = {
                    "ts": datetime.now().isoformat(),
                    "task": task[:200],
                    "confidence": evaluation.get("confidence", 0.5),
                    "quality": evaluation.get("quality", "medium"),
                    "learned": evaluation.get("learned", [])
                }
                history = self.gcs_client.read_json(f"agents/performance/{self.name}.json") or {"history": []}
                history["history"].append(perf_log)
                self.gcs_client.upload_json(history, f"agents/performance/{self.name}.json")

                # Sincroniza registry global
                registry = self.gcs_client.read_json("agents/registry.json")
                if registry:
                    for a in registry.get("agents", []):
                        if a["agent_name"] == self.name:
                            a["metrics"] = agent_data["metrics"]
                            break
                    self.gcs_client.upload_json(registry, "agents/registry.json")

            return result, evaluation
        except Exception as e:
            return f"Erro na execução do agente {self.name}: {str(e)}", {}
