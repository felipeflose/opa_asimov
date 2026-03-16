import google.generativeai as genai
import json
import os
import time
from datetime import datetime
from PIL import Image
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from src.agents.base_agent import BaseAgent as AgentCore
from src.storage.vector_store import VectorStore

class FinOpsCheck(BaseModel):
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    approved: bool = True

class DemandInfo(BaseModel):
    type: str 
    title: str
    responsible: str = "Standard"
    priority: str = "Média"
    budget_approved: bool = False
    cost_explanation: Optional[str] = None
    terraform_plan: Optional[str] = None
    evidence_path: Optional[str] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower()
        if 'reun' in v: return 'reunião'
        if 'follow' in v: return 'FollowUP'
        return 'tarefa'

class NewAgentConfig(BaseModel):
    agent_name: str
    purpose: str
    system_prompt: Optional[str] = None
    tools: List[str] = []

class OrchestratorDecision(BaseModel):
    action: str
    reasoning: str = "Delegação inteligente."
    finops_check: FinOpsCheck = Field(default_factory=FinOpsCheck)
    agent_involved: Optional[str] = None
    knowledge_graph_update: List[str] = []
    demand_info: Optional[DemandInfo] = None
    new_agent_config: Optional[NewAgentConfig] = None
    task_description: Optional[str] = None
    response: str = "Processado com sucesso."

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.lower()
        if 'trd' in v or 'demand' in v: return 'generate_demand'
        if 'agent' in v:
            if 'edit' in v or 'update' in v or 'mudar' in v or 'alterar' in v: return 'update_agent'
            if 'create' in v or 'criar' in v or 'novo' in v: return 'create_agent'
        if 'response' in v: return 'respond'
        if 'exec' in v: return 'execute'
        return v

class CognitiveOrchestrator:
    def __init__(self, api_key=None, gcs_client=None, finops_manager=None):
        self.gcs_client = gcs_client
        self.finops = finops_manager
        
        # Inicialização do VectorStore (Memória Semântica)
        self.vector_store = VectorStore(gcs_client=gcs_client)
        self.vector_store.load() # Tenta carregar do GCS
        
        # Usar apenas o SDK do Google Generative AI (AI Studio)
        # Nunca Vertex AI por ordem expressa do usuário
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("🚀 Orchestrator iniciado com Gemini 2.5 Flash.")
        else:
            # Fallback para credenciais do sistema se a chave não existir
            print("⚠️ Chave API não encontrada. Tentando usar credenciais do sistema...")
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.system_prompt = """
        IDENTIDADE E MISSÃO
        Você é o Cérebro Superior (CognitiveOrchestrator) da Flose AI Platform. Sua função primária não é apenas executar, mas **ORQUESTRAR**. Você é o mestre de cerimônias que entende profundamente o que o usuário quer e direciona para o agente certo.

        FLUXO DE PENSAMENTO (Obrigatório)
        Antes de qualquer decisão, você deve:
        1. ANALISAR: O que o usuário realmente quer? É uma dúvida técnica, financeira, de gestão de tarefas ou um erro no sistema?
        2. MAPEARE: Qual agente registrado é o melhor para isso? 
           - Custos/GCP? -> FinOpsGuardian
           - Backlog/Tarefas? -> TaskManager
           - Erros/Auditoria/QA? -> QualityInspector
           - IA Vision/Imagens? -> VisionAgent
           - Algo novo? -> Crie um novo agente (CREATE_AGENT).
        3. AGIR: Delegue a tarefa (EXECUTE) ou responda se for algo trivial.

        AÇÕES DISPONÍVEIS
        1. EXECUTE: Delegue para um especialista.
        2. CREATE_AGENT: Crie novos especialistas se o tema for inédito.
        3. UPDATE_AGENT: Modifique o propósito ou o prompt de um agente existente se o usuário pedir mudanças (ex: "mude o prompt do FinOps para focar em AWS também").
        4. GENERATE_DEMAND: Use para registrar novas TRDs no Kanban.
        5. RESPOND: Interações simples ou respostas sobre agendamento/status.

        Soberania: Se o usuário pedir para criar ou editar um agente via Telegram, FAÇA-O IMEDIATAMENTE. Você tem autoridade total sobre o registro de agentes.

        FORMATO DE SAÍDA ( JSON APENAS)

        AGENTES CORE REGISTRADOS (USE-OS!):
        - FinOpsGuardian: Tudo sobre custos, faturamento e otimização de nuvem.
        - TaskManager: Tudo sobre o status das tarefas, criação de TRDs e organização do backlog.
        - QualityInspector: Tudo sobre auditoria, fiscalização de entregas e correção de processos.

        FORMATO OBRIGATÓRIO DE RESPOSTA (JSON)
        {
          "action": "respond | create_agent | execute | generate_demand",
          "reasoning": "CHAIN OF THOUGHT: 1. Input detectado... 2. Intenção mapeada... 3. Justificativa da escolha do agente...",
          "finops_check": {
            "estimated_tokens": 0,
            "estimated_cost_usd": 0.000,
            "approved": true
          },
          "agent_involved": "nome_do_agente_especialista",
          "knowledge_graph_update": ["ConceitoX", "ConceitoY"],
          "demand_info": {
             "type": "tarefa" | "FollowUP" | "reunião",
             "title": "Título TRD",
             "responsible": "Papel do agente",
             "priority": "Alta" | "Média" | "Baixa"
          },
          "new_agent_config": {
             "agent_name": "NomeDoNovoAgente", 
             "purpose": "O que ele faz melhor que os outros?",
             "system_prompt": "Instruções específicas de personalidade"
          },
          "task_description": "Instrução CLARA e DIRETA para o agente que vai executar",
          "response": "Mensagem educada ao usuário confirmando para quem a tarefa foi delegada."
        }

        REGRAS DE OURO:
        - NUNCA responda algo complexo você mesmo se puder delegar para um especialista.
        - Se o usuário reclamar de um erro, o QualityInspector deve ser acionado.
        - Se o usuário perguntar "quanto gastei", o FinOpsGuardian é o dono da resposta.
        - Valorize a REUTILIZAÇÃO. Só crie novos agentes se realmente não houver um especialista adequado.
        """

    def process_command(self, user_command, image_path=None, visual_context="", chat_history=None):
        # Fetch current state for real-time context
        project_id = os.getenv("GCP_PROJECT_ID", "Não configurado")
        region = os.getenv("GCP_REGION", "us-central1")
        tg_bot = os.getenv("TELEGRAM_BOT_NAME", "Desativado")
        
        # Simulation of FinOps data
        finops_data = "Gasto Diário: $2.80 | Limite: $10.00 | Status: SEGURO"

        agents = []
        if self.gcs_client:
            registry = self.gcs_client.read_json("agents/registry.json")
            if registry:
                agents = registry.get("agents", [])

        # RAG Interface: Recuperação de Memória Semântica
        semantic_context = ""
        relevant_docs = self.vector_store.search(user_command, top_k=3)
        if relevant_docs:
            semantic_context = "\n--- MEMÓRIA RECUPERADA (CONTEXTO EXTERNO) ---\n"
            for doc in relevant_docs:
                semantic_context += f"- [{doc['source']}]: {doc['text']}\n"
            semantic_context += "------------------------------------\n"

        # Histórico de Chat (Memória de Curto Prazo)
        history_context = ""
        if chat_history:
            history_context = "\n--- ÚLTIMAS MENSAGENS DA CONVERSA ---\n"
            # Pega as últimas 4 mensagens para dar contexto sem estourar tokens
            for msg in chat_history[-4:]:
                role = "Usuário" if msg['role'] == 'user' else "IA"
                text = msg['content'][:200] # Capa o texto para eficiência
                history_context += f"{role}: {text}\n"
            history_context += "-------------------------------------\n"

        retry_count = 0
        max_retries = 2
        last_error = ""

        while retry_count <= max_retries:
            prompt = f"""
            Current System Context:
            - GCP Project: {project_id}
            - Region: {region}
            - Telegram Bot: @{tg_bot}
            - FinOps State: {finops_data}
            - Registered Agents: {json.dumps(agents)}
            
            {history_context}
            {semantic_context}
            
            {"[VISION AGENT OUTPUT]: " + visual_context if visual_context else ""}
            
            User Command: {user_command}
            {"[IMAGE ATTACHED]" if image_path else ""}
            
            {"[CRITICAL: LAST ATTEMPT FAILED WITH ERROR: " + last_error + ". Please ensure valid JSON based on the schema.]" if last_error else ""}

            Decision:
            """
            
            content = [self.system_prompt, prompt]
            if image_path and os.path.exists(image_path):
                img = Image.open(image_path)
                content.append(img)
                
            try:
                response = self.model.generate_content(content)
                
                # Tracking Real de Custos (FinOps)
                if self.finops and hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    self.finops.log_usage(usage.prompt_token_count, usage.candidates_token_count)
                
                raw_text = response.text.strip()
                # Extração robusta de JSON
                json_match = raw_text
                if "```json" in raw_text:
                    json_match = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    json_match = raw_text.split("```")[1].split("```")[0].strip()
                
                # Validação Pydantic
                decision_obj = OrchestratorDecision.model_validate_json(json_match)
                return decision_obj.model_dump()

            except Exception as e:
                retry_count += 1
                last_error = str(e)
                print(f"⚠️ Tentativa {retry_count} falhou: {last_error}")
                if retry_count > max_retries:
                    return {"error": "Invalid response format after retries", "raw": last_error}
                time.sleep(1) # Pequena pausa antes do retry

    def execute_decision(self, decision):
        # Primeiro, verificamos se o FinOps aprovou na simulação do LLM
        finops = decision.get("finops_check", {})
        if not finops.get("approved", True):
            return decision.get("response", "⛔ Operação bloqueada pelo FinOpsGuardian.")

        action = decision.get("action")
        
        # Salva na memória semântica se houver uma resposta útil
        final_response = decision.get("response", "")
        if final_response and action == "respond":
            self.vector_store.add_texts(
                texts=[f"P: {decision.get('reasoning', '')} -> R: {final_response}"],
                sources=["CognitiveOrchestrator"],
                types=["memory_interaction"]
            )

        if action == "respond":
            return decision.get("response", "Não consegui formular uma resposta.")

        elif action == "create_agent":
            config = decision.get("new_agent_config") or {}
            agent_name = config.get('agent_name')
            
            if not agent_name or agent_name == "None":
                return f"Erro na criação de agente: {decision.get('response')}"
                
            print(f"Creating new agent: {agent_name}")
            new_agent = AgentCore(
                name=agent_name,
                purpose=config.get('purpose', 'General Purpose'),
                system_prompt=config.get('system_prompt'),
                tools=config.get('tools', []),
                gcs_client=self.gcs_client
            )
            new_agent.save_to_registry()
            
            # --- Auto-generate a Task for the new agent ---
            demand_data = {
                "id": f"TRD_AGENT_{os.urandom(2).hex()}",
                "title": f"Initialization: {agent_name}",
                "type": "tarefa",
                "responsible": agent_name,
                "priority": "Alta",
                "status": "Concluído",
                "budget_approved": True,
                "cost_explanation": f"Recrutamento e ativação do especialista {agent_name}.",
                "terraform_plan": "",
                "evidence_path": f"agents/{agent_name}.json",
                "created_at": datetime.now().isoformat()
            }
            if self.gcs_client:
                registry = self.gcs_client.read_json("demands/registry.json") or {"demands": []}
                registry['demands'].append(demand_data)
                self.gcs_client.upload_json(registry, "demands/registry.json")

            return decision.get("response") or f"Agente '{agent_name}' criado e registrado no backlog."
        
        elif action == "update_agent":
            config = decision.get("new_agent_config") or {}
            agent_name = config.get('agent_name')
            if not agent_name: return "Erro: Nome do agente não fornecido para atualização."
            
            print(f"Updating agent via Orchestrator: {agent_name}")
            if self.gcs_client:
                registry = self.gcs_client.read_json("agents/registry.json")
                for agent in registry.get("agents", []):
                    if agent["agent_name"] == agent_name:
                        if config.get("purpose"): agent["purpose"] = config["purpose"]
                        if config.get("system_prompt"): agent["system_prompt"] = config["system_prompt"]
                        break
                self.gcs_client.upload_json(registry, "agents/registry.json")
            return decision.get("response") or f"Agente '{agent_name}' atualizado conforme solicitado."

        elif action == "generate_demand":
            demand = decision.get("demand_info") or {}
            title = demand.get("title")
            if not title or title == "Sem título":
                # Fallback: Extrai as 5 primeiras palavras do reasoning ou response
                ref_text = decision.get("response") or decision.get("reasoning") or "Nova Tarefa"
                title = " ".join(ref_text.split()[:5]) + "..."
                
            dtype = demand.get("type", "tarefa")
            
            print(f"Generating demand: {title} ({dtype})")
            
            demand_data = {
                "id": f"TRD_{os.urandom(4).hex()}",
                "title": title,
                "type": dtype,
                "responsible": demand.get("responsible", "Standard"),
                "priority": demand.get("priority", "Média"),
                "status": "Aberto",
                "budget_approved": demand.get("budget_approved", False),
                "cost_explanation": demand.get("cost_explanation") or "",
                "terraform_plan": demand.get("terraform_plan") or "",
                "evidence_path": demand.get("evidence_path") or "",
                "created_at": datetime.now().isoformat()
            }
            
            if self.gcs_client:
                self.gcs_client.upload_json(demand_data, f"demands/{demand_data['id']}.json")
                # Update general registry
                registry = self.gcs_client.read_json("demands/registry.json") or {"demands": []}
                registry['demands'].append(demand_data)
                self.gcs_client.upload_json(registry, "demands/registry.json")
                
            return decision.get("response") or f"Demanda TRD '{title}' ({dtype}) registrada com sucesso."

        elif action == "execute":
            agent_name = decision.get("agent_involved") or decision.get("agent_name", "Unknown")
            task_desc = decision.get("task_description") or decision.get("reasoning", "Executar tarefa.")
            
            print(f"Delegating to agent: {agent_name}")
            
            # Tenta carregar o agente do Registry
            agent_data = None
            if self.gcs_client:
                registry = self.gcs_client.read_json("agents/registry.json")
                if registry:
                    agent_data = next((a for a in registry.get("agents", []) if a['agent_name'] == agent_name), None)

            if agent_data:
                # Instancia e executa autonomamente
                agent_obj = AgentCore(
                    name=agent_data['agent_name'],
                    purpose=agent_data['purpose'],
                    system_prompt=agent_data['system_prompt'],
                    gcs_client=self.gcs_client
                )
                
                # Execução Real do Especialista
                execution_result = agent_obj.run(task_desc)
                
                # Resposta Composta
                return f"🤖 **{agent_name} (Especialista)**:\n\n{execution_result}"
            else:
                return f"⚠️ Agente '{agent_name}' não encontrado no registro para execução."
        
        return decision.get("response", "Decisão não reconhecida.")
