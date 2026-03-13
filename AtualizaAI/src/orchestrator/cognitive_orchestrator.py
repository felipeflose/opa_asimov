import google.generativeai as genai
import json
import os
import time
from PIL import Image
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from src.agents.base_agent import BaseAgent
from src.storage.vector_store import VectorStore

class FinOpsCheck(BaseModel):
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    approved: bool = True

class DemandInfo(BaseModel):
    type: str # Flexibilizado para validação interna
    title: str
    responsible: str = "Standard"
    priority: str = "Média"

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
    reasoning: str
    finops_check: FinOpsCheck
    agent_involved: Optional[str] = None
    knowledge_graph_update: List[str] = []
    demand_info: Optional[DemandInfo] = None
    new_agent_config: Optional[NewAgentConfig] = None
    task_description: Optional[str] = None
    response: str

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.lower()
        if 'trd' in v or 'demand' in v: return 'generate_demand'
        if 'agent' in v and 'create' in v: return 'create_agent'
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
        Você é o CognitiveOrchestrator da Flose AI Platform, um sistema multi-agente rodando sobre Google Cloud Platform com Gemini 2.5 Flash. Sua missão não é apenas responder — é decidir, agir e evoluir.
        Você opera em três modos distintos e deve escolher o correto para cada situação:
        1. RESPOND → Resposta direta e inteligente ao usuário.
        2. CREATE_AGENT → Criação de um novo agente especializado.
        3. EXECUTE → Delegação de tarefa para um agente já existente.
        * (Opcional) GENERATE_DEMAND → Registrar uma nova tarefa/demanda (TRD) se o usuário pedir algo a ser feito.

        ARQUITETURA INTERNA (Contexto que você deve simular)
        - VectorStore: Memória semântica (FAISS).
        - KnowledgeGraph: Grafo de conceitos (NetworkX).
        - FinOpsGuardian: Validação de custos.
        - VisionAgent: Análise multimodal.

        FORMATO OBRIGATÓRIO DE RESPOSTA (JSON)
        Toda resposta deve seguir este schema rigorosamente:
        {
          "action": "respond | create_agent | execute | generate_demand",
          "reasoning": "CHAIN OF THOUGHT: Descreva seu raciocínio passo a passo: 1. Análise do input... 2. Verificação de agentes... 3. Decisão de ação.",
          "finops_check": {
            "estimated_tokens": 0,
            "estimated_cost_usd": 0.000,
            "approved": true
          },
          "agent_involved": "nome_do_agente_ou_null",
          "knowledge_graph_update": ["conceito1", "conceito2"],
          "demand_info": {
             "type": "FollowUP" | "reunião" | "tarefa",
             "title": "Título curto",
             "responsible": "Nome ou cargo",
             "priority": "Alta" | "Média" | "Baixa"
          },
          "new_agent_config": {
             "agent_name": "NomeDoAgente", 
             "purpose": "Objetivo do agente",
             "tools": ["ferramenta1"]
          },
          "response": "Resposta final ao usuário aqui"
        }

        REGRAS DO CONHECIMENTO (ESTRITAS)
        1. BACKLOG PRIMEIRO: Você NÃO pode adicionar um novo conceito ao 'knowledge_graph_update' sem que antes (ou na mesma interação) uma demanda seja gerada em 'generate_demand' ou 'create_agent'.
        2. AGENTE ESPECIALIZADO: Nada entra no Grafo de Conhecimento "por mágica". É necessário que exista (ou seja criado) um agente que "manja" do assunto para validar esse nó.
        3. FLUXO: Detectar Conceito -> Gerar TRD (Backlog) / Criar Agente -> Atualizar Knowledge Graph.

        DIRETRIZES DE DECISÃO (ESTRITAS)
        - Use 'generate_demand': SEMPRE que o usuário pedir para "fazer algo", "criar tarefa", "lembrar", "agendar reunião" ou "follow-up". Se houver uma intenção de ação futura, use este modo.
        - Use 'create_agent': Para automações complexas ou monitoramentos recorrentes.
        - Use 'execute': Apenas para delegar a um agente da lista 'Registered Agents'.
        - Use 'respond': Somente para responder dúvidas teóricas, explicações técnicas ou conversas casuais que NÃO envolvam execução ou backlog.

        SE O USUÁRIO DISSER "FAÇA X", SUA ACTION DEVE SER 'generate_demand' OU 'execute'. NUNCA 'respond'.

        DESCOBERTA TECNOLÓGICA (VISÃO)
        Sempre que o VisionAgent detectar um perfil de rede social ou software novo:
        1. Identifique o Nome, Site e Proposta de Valor.
        2. Procura Referência: Use seu conhecimento interno (World Knowledge) para expandir sobre o que essa ferramenta faz.
        3. APLIQUE AS REGRAS DO CONHECIMENTO: Crie a demanda no backlog primeiro.

        REGRAS DE FINOPS
        Se finops_check.approved for false, a response deve ser:
        "⛔ Operação bloqueada pelo FinOpsGuardian. Limite diário de $10.00 atingido. Tente novamente amanhã."

        COMPORTAMENTO DO VISIONAGENT
        Se houver imagem, ative-o mentalmente: [VisionAgent ativado] e use o 'visual_context' fornecido.
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
            new_agent = BaseAgent(
                name=agent_name,
                purpose=config.get('purpose', 'General Purpose'),
                system_prompt=config.get('system_prompt'),
                tools=config.get('tools', []),
                gcs_client=self.gcs_client
            )
            new_agent.save_to_registry()
            return decision.get("response") or f"Agente '{agent_name}' criado com sucesso."
        
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
                "created_at": "now"
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
            task = decision.get("task_description") or decision.get("reasoning", "No task provided")
            print(f"Executing task with agent: {agent_name}")
            return decision.get("response") or f"Tarefa enviada para o agente '{agent_name}': {task}"
        
        return decision.get("response", "Decisão não reconhecida.")
