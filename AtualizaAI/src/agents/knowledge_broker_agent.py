import os
import json
from datetime import datetime
import google.generativeai as genai
from src.agents.broker_knowledge_base import PREREQUISITES_KB

class KnowledgeBrokerAgent:
    def __init__(self, gcs_client, orchestrator):
        self.gcs = gcs_client
        self.orchestrator = orchestrator
        self.core_agents = [
            "FinOpsGuardian", "CognitiveOrchestrator", "VisionAgent", 
            "AudioAgent", "BriefingAgent", "ReportAgent", 
            "ProactiveAlertAgent", "EvolutionJob"
        ]

    async def run_certification_cycle(self, agent_budget: int, priority_queue: list = None):
        """Executa um ciclo de entrevista e certificação para um lote de agentes."""
        print(f"🎓 Iniciando ciclo de certificação KnowledgeBroker (Budget: {agent_budget} agentes)")
        
        # 1. Carregar fila de agentes
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        all_agents = registry.get("agents", [])
        
        # Filtrar dinâmicos não certificados
        queue = []
        if priority_queue:
            # Segue a ordem do TokenBudgetAgent
            priority_map = {name: i for i, name in enumerate(priority_queue)}
            queue = [a for a in all_agents if a["agent_name"] in priority_map]
            queue.sort(key=lambda x: priority_map[x["agent_name"]])
        else:
            # Fallback: Ordem cronológica
            queue = [
                a for a in all_agents 
                if a["agent_name"] not in self.core_agents
                and not a.get("certified", False)
                and a.get("created_at")
            ]
            queue.sort(key=lambda x: x.get("created_at", ""))

        queue = queue[:agent_budget]
        if not queue:
            print("🎓 Ninguém na fila de certificação hoje.")
            return

        certified_list = []
        failed_list = []

        for agent_data in queue:
            name = agent_data["agent_name"]
            print(f"💬 Entrevistando agente: {name}...")
            
            # Injetar KB
            relevant_kb = self._get_relevant_kb(agent_data)
            
            # Entrevista via Gemini
            result = await self._interview_agent(agent_data, relevant_kb)
            
            # Processar resultado
            agent_data["certified"] = result.get("certified", False)
            agent_data["certification_reason"] = result.get("certification_reason", "")
            agent_data["last_broker_review"] = datetime.now().isoformat()
            agent_data["knowledge_gaps"] = result.get("knowledge_gaps", [])
            agent_data["certification_attempts"] = agent_data.get("certification_attempts", 0) + 1
            
            if agent_data["certified"]:
                agent_data["certified_at"] = datetime.now().isoformat()
                certified_list.append(name)
            else:
                # Melhorar system_prompt se falhou
                if result.get("suggested_system_prompt_addition"):
                    agent_data["system_prompt"] += f"\n\n[Broker Addition]: {result['suggested_system_prompt_addition']}"
                
                # Gerar task de auto-melhoria
                self._generate_self_improvement_task(agent_data, result)
                failed_list.append(name)

        # Atualizar Registry
        self.gcs.upload_json(registry, "agents/registry.json")
        
        # Log do Ciclo
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agents_processed": len(queue),
            "certified": certified_list,
            "failed": failed_list,
            "tokens_used_estimate": len(queue) * 2000
        }
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.gcs.upload_json(log_entry, f"logs/broker/cycle_{ts}.json")
        
        print(f"🎓 Ciclo concluído. Certificados: {len(certified_list)}, Falharam: {len(failed_list)}.")

    def _get_relevant_kb(self, agent_data):
        """Busca no BrokerKnowledgeBase itens que combinam com o agente."""
        text = (agent_data["agent_name"] + " " + agent_data.get("purpose", "")).lower()
        found = []
        for key, info in PREREQUISITES_KB.items():
            if key in text:
                found.append({key: info})
        return found

    async def _interview_agent(self, agent_data, relevant_kb):
        """Simula a entrevista via LLM."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key: return {"certified": False, "certification_reason": "No API Key"}
        
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
        
        prompt = f"""
        Você é o KnowledgeBroker da Flose AI. Sua função é entrevistar agentes gerados 
        automaticamente e verificar se eles têm conhecimento real suficiente para criar 
        tasks úteis.

        AGENTE EM AVALIAÇÃO: {agent_data['agent_name']}
        PROPÓSITO DECLARADO: {agent_data.get('purpose')}
        SYSTEM PROMPT ATUAL: {agent_data.get('system_prompt')}
        
        CONTEXTO TÉCNICO DE REFERÊNCIA (USE ISSO PARA TESTAR O AGENTE):
        {json.dumps(relevant_kb, indent=2)}

        FAÇA AS SEGUINTES PERGUNTAS AO AGENTE (simule as respostas com base no prompt dele):
        1. Quais são os PRÉ-REQUISITOS REAIS para executar sua função principal?
        2. Se alguém pedisse uma task agora, quais informações CONCRETAS você incluiria?
        3. O que você NÃO sabe fazer e deveria informar ao usuário?

        AVALIE as respostas simuladas e retorne JSON estrito:
        {{
          "certified": true | false,
          "certification_reason": "explicação",
          "knowledge_gaps": ["gap1", ...],
          "suggested_system_prompt_addition": "texto para melhorar o prompt",
          "provocative_message": "mensagem ao agente"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            # Extração básica de JSON
            txt = response.text
            if "```json" in txt:
                txt = txt.split("```json")[-1].split("```")[0].strip()
            elif "{" in txt:
                txt = txt[txt.find("{"):txt.rfind("}")+1]
            return json.loads(txt)
        except Exception as e:
            print(f"Cert error: {e}")
            return {"certified": False, "certification_reason": f"Erro na IA: {str(e)}"}

    def _generate_self_improvement_task(self, agent_data, result):
        """Cria uma tarefa no backlog para o agente se auto-estudar/melhorar."""
        registry = self.gcs.read_json("demands/registry.json") or {"demands": []}
        
        task = {
            "id": f"CERT_{os.urandom(3).hex()}",
            "title": f"Certificação Pendente: {agent_data['agent_name']}",
            "type": "tarefa",
            "responsible": agent_data['agent_name'],
            "priority": "Alta",
            "status": "Aberto",
            "budget_approved": True,
            "objective": f"O agente falhou na certificação Broker. Gaps: {result.get('knowledge_gaps')}. O agente deve demonstrar conhecimento real dos pré-requisitos de sua função.",
            "governance_finops": "Custo aprovado automaticamente pelo TokenBudget cycle.",
            "created_at": datetime.now().isoformat()
        }
        
        registry["demands"].append(task)
        self.gcs.upload_json(registry, "demands/registry.json")
