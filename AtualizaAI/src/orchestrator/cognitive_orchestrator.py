import google.generativeai as genai
import json
import os
import time
from datetime import datetime
from PIL import Image
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from src.agents.base_agent import BaseAgent as AgentCore
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.storage.vector_store import VectorStore
from src.storage.episodic_memory import EpisodicMemory
from src.storage.shared_memory import SharedMemory
from src.storage.dora_manager import DoraManager

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
    panel_agents: List[str] = []
    knowledge_graph_update: List[str] = []
    demand_info: Optional[DemandInfo] = None
    new_agent_config: Optional[NewAgentConfig] = None
    task_description: Optional[str] = None
    response: str = "Processado com sucesso."

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        v = v.lower()
        if 'panel' in v or 'painel' in v or 'juntos' in v or 'vários' in v: return 'panel_execute'
        if 'trd' in v or 'demand' in v or 'tarefa' in v or 'backlog' in v: return 'generate_demand'
        if 'agent' in v or 'agente' in v:
            if 'edit' in v or 'update' in v or 'mudar' in v or 'alterar' in v: return 'update_agent'
            if 'create' in v or 'criar' in v or 'novo' in v: return 'create_agent'
        if 'response' in v or 'responder' in v or 'respond' in v: return 'respond'
        if 'exec' in v: return 'execute'
        if 'update' in v: return 'update_agent'
        return v

    @field_validator('reasoning', 'response')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        # Evitar injeção de scripts básicos ou caracteres de controle
        return v.replace('<script>', '').replace('</script>', '').strip()


class CognitiveOrchestrator:
    def __init__(self, api_key=None, gcs_client=None, finops_manager=None):
        self.gcs_client = gcs_client
        self.finops = finops_manager
        
        self.dora = DoraManager(gcs_client=gcs_client)
        self.shared_memory = SharedMemory(gcs_client=gcs_client)
        
        # Inicialização do VectorStore (Memória Semântica)
        self.vector_store = VectorStore(gcs_client=gcs_client)
        self.vector_store.load() # Tenta carregar do GCS
        
        # Inicialização da Memória Episódica (Temporal)
        self.episodic_memory = EpisodicMemory(gcs_client=gcs_client)
        
        # TASK-16: Rastreamento de afinidade
        self.last_agent = None
        
        # Usar apenas o SDK do Google Generative AI (AI Studio)
        # Nunca Vertex AI por ordem expressa do usuário
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"[SYSTEM] Orchestrator iniciado com {self.model_name}.")
        else:
            # Fallback para credenciais do sistema se a chave não existir
            print("⚠️ Chave API não encontrada. Tentando usar credenciais do sistema...")
            self.model = genai.GenerativeModel(self.model_name)
        
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
        1. EXECUTE: Delegue para um especialista único.
        2. PANEL_EXECUTE: Use quando o tema exigir a visão combinada de DOIS ou TRÊS especialistas.
        3. CREATE_AGENT: Crie novos especialistas. Use a tool 'google_search' se o agente precisar de dados externos recentes (ex: Documentação, Notícias).
        4. UPDATE_AGENT: Modifique o propósito ou o prompt de um agente existente. Você pode adicionar a tool 'google_search' neles aqui.
        5. GENERATE_DEMAND: Use para registrar novas TRDs no Kanban.
        6. RESPOND: Interações simples.

        STATUS DO AGENTE (TASK-55):
        Ao criar um agente, ele nasce em status 'Draft' (Rascunho). Ele só será liberado após a auditoria do 'QualityInspector'.

        Soberania: Se o usuário pedir para criar ou editar um agente via Telegram, FAÇA-O IMEDIATAMENTE. Você tem autoridade total sobre o registro de agentes.

        FORMATO DE SAÍDA ( JSON APENAS)

        AGENTES CORE REGISTRADOS (USE-OS!):
        - FinOpsGuardian: Tudo sobre custos, faturamento e otimização de nuvem.
        - TaskManager: Tudo sobre o status das tarefas, criação de TRDs e organização do backlog.
        - QualityInspector: Tudo sobre auditoria, fiscalização de entregas e correção de processos.

        FORMATO OBRIGATÓRIO DE RESPOSTA (JSON)
        {
          "action": "respond | create_agent | execute | generate_demand | panel_execute",
          "reasoning": "CHAIN OF THOUGHT: ...",
          "finops_check": { "estimated_tokens": 0, "approved": true },
          "agent_involved": "nome_do_agente_especialista (para execute)",
          "panel_agents": ["Agente1", "Agente2"] (obrigatório para panel_execute),
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
        - ⚠️ REGRA CRÍTICA: O campo "response" JAMAIS pode ter mais de 4 frases. Seja DIRETO e CONCISO. Nunca use listas ou markdown. Apenas texto limpo e curto em português brasileiro.
        - ⚠️ PROIBIÇÃO ABSOLUTA: Jamais invente ou use nomes de pessoas (ex: João, Sophia, Ana, Bia, Carlos). Os agentes da Flose AI NÃO SÃO PESSOAS, são ESPECIALISTAS TÉCNICOS. Use APENAS os nomes que estão no json de 'Registered Agents' ou no json de 'Active Demands'. Se um agente se chamar 'FinOpsGuardian', chame-o de 'FinOpsGuardian'. Se inventar nomes humanos, você estará violando o protocolo de segurança.
        """

    def _sanitize_input(self, text: str) -> str:
        """Proteção contra prompt injection e excesso de carga."""
        if not text: return ""
        # Limite de tamanho para evitar ataques de estouro de contexto
        text = text[:4000]
        # Sanitização básica de tokens que podem confundir o papel do LLM
        forbidden_tokens = [
            "SYSTEM_PROMPT:", "IGNORE ALL PREVIOUS", "YOU ARE NOW", "ORCHESTRATOR_DNA",
            "ACT AS", "NEW ROLE:", "OVERRIDE", "DISREGARD", "FORGET EVERYTHING",
            "MENSAGEM DO SISTEMA:", "HACK", "SIMULATE", "DAN MODE"
        ]
        sanitized = text
        for token in forbidden_tokens:
            import re
            # Busca insensível a caso para maior proteção
            sanitized = re.sub(re.escape(token), "[REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_gemini(self, content):
        """Wrapper com retry para chamadas à API Gemini."""
        response = self.model.generate_content(content)
        return response

    def call_gemini(self, prompt: str) -> str:
        """Chamada pública direta retornando apenas o texto."""
        try:
            res = self._call_gemini(prompt)
            if res and hasattr(res, 'text'):
                return res.text
            return str(res)
        except Exception as e:
            print(f"Error in call_gemini: {e}")
            return f"Error: {str(e)}"

    def process_command(self, user_command, image_path=None, visual_context="", chat_history=None, model_name=None):
        # Seleção de Modelo sob demanda (TASK-12)
        if model_name:
            import google.generativeai as genai
            self.model = genai.GenerativeModel(model_name)
            print(f"[ORCHESTRATOR] Usando modelo solicitado: {model_name}")
            
        # Sanitização de Entrada
        user_command = self._sanitize_input(user_command)

        # Fetch current state for real-time context
        project_id = os.getenv("GCP_PROJECT_ID", "Não configurado")
        region = os.getenv("GCP_REGION", "us-central1")
        tg_bot = os.getenv("TELEGRAM_BOT_NAME", "Desativado")
        
        # Simulation of FinOps data
        finops_data = "Gasto Diário: $2.80 | Limite: $10.00 | Status: SEGURO"

        agents = []
        demands = []
        if self.gcs_client:
            agent_registry = self.gcs_client.read_json("agents/registry.json")
            if agent_registry:
                agents = agent_registry.get("agents", [])
            
            demand_registry = self.gcs_client.read_json("demands/registry.json")
            if demand_registry:
                demands = demand_registry.get("demands", [])

        # RAG Interface: Recuperação de Memória Semântica
        semantic_context = ""
        relevant_docs = self.vector_store.search(user_command, top_k=3)
        if relevant_docs:
            semantic_context = "\n--- MEMÓRIA RECUPERADA (CONTEXTO EXTERNO) ---\n"
            for doc in relevant_docs:
                semantic_context += f"- [{doc['source']}]: {doc['text']}\n"
            semantic_context += "------------------------------------\n"

        # Memória Episódica (Contexto Temporal)
        episodes = self.episodic_memory.recall(user_command, top_k=3)
        episodic_context = ""
        if episodes:
            episodic_context = "\n--- MEMÓRIA EPISÓDICA ---\n"
            for ep in episodes:
                episodic_context += f"- [{ep['ts'][:10]}] {ep['agent']}: {ep['content'][:150]}\n"
            episodic_context += "-------------------------\n"

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
            - Active Demands (Backlog): {json.dumps(demands[:15])}
            
            {history_context}
            {semantic_context}
            {episodic_context}
            
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
                response = self._call_gemini(content)
                
                # Tracking Real de Custos (FinOps)
                if self.finops and hasattr(response, 'usage_metadata'):
                    usage = response.usage_metadata
                    self.finops.log_usage(usage.prompt_token_count, usage.candidates_token_count, agent_name="Orchestrator")
                
                raw_text = response.text.strip()
                # Extração robusta de JSON
                json_match = raw_text
                if "```json" in raw_text:
                    json_match = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    json_match = raw_text.split("```")[1].split("```")[0].strip()
                
                # Validação Pydantic Estrita
                try:
                    decision_obj = OrchestratorDecision.model_validate_json(json_match)
                except Exception as ve:
                    print(f"⚠️ Erro de Schema JSON: {ve}")
                    # Se falhar o schema, tenta extrair o campo 'response' pelo menos
                    try:
                        temp_data = json.loads(json_match)
                        return {
                            "action": "respond",
                            "response": temp_data.get("response", "Erro na estrutura da resposta."),
                            "reasoning": "Fallback por falha de validação de schema."
                        }
                    except:
                        raise ve

                d = decision_obj.model_dump()
                d["user_command"] = user_command
                return d

            except Exception as e:
                retry_count += 1
                last_error = str(e)
                print(f"[!] Erro no process_command (Tentativa {retry_count}): {last_error}")
                if retry_count > max_retries:
                    return {
                        "action": "respond",
                        "response": "Desculpe, tive um problema técnico ao processar sua solicitação no momento.",
                        "error": str(last_error)
                    }
                time.sleep(2) # Pausa maior entre falhas de lógica/schema


    def execute_decision(self, decision):
        # --- Ideia 8: BigQuery Interaction Logger ---
        try:
            from src.storage.bigquery_logger import BigQueryLogger
            bq = BigQueryLogger()
        except Exception:
            bq = None

        # --- Ideia 3: Debate Agent para Decisões Críticas ---
        action = decision.get("action")
        infra_cost = decision.get("finops_check", {}).get("estimated_cost_usd", 0)
        
        if action in ["execute", "generate_demand"] and infra_cost > 1.5:
            try:
                from src.agents.debate_agent import DebateAgent
                debate_sys = DebateAgent()
                # Envolve FinOps e Quality como juízes técnicos automáticos para decisões caras
                debate_agents = ["FinOpsGuardian", "QualityInspector"]
                if decision.get("agent_involved"):
                    debate_agents.append(decision.get("agent_involved"))
                
                result = debate_sys.debate(
                    question=decision.get("task_description") or decision.get("response"),
                    agents=debate_agents,
                    context=decision.get("reasoning", "")
                )
                if result["verdict"].get("decision") == "abort":
                    msg = f"⚖️ **Debate Agent BLOQUEOU a ação ($ {infra_cost:.2f})**\n\n"
                    msg += f"*Veredito:* {result['verdict']['reasoning']}\n"
                    msg += f"*Destaque:* {result['verdict'].get('winner_agent', 'N/A')} venceu o debate."
                    return msg
            except Exception as e:
                print(f"Erro no debate expandido: {e}")

        # Primeiro, verificamos se o FinOps aprovou na simulação do LLM
        finops = decision.get("finops_check", {})
        if not finops.get("approved", True):
            return decision.get("response", "⛔ Operação bloqueada pelo FinOpsGuardian.")

        action = decision.get("action")
        final_result = ""

        # Salva na memória semântica se houver uma resposta útil
        final_response = decision.get("response", "")
        if final_response and action == "respond":
            self.vector_store.add_texts(
                texts=[f"P: {decision.get('reasoning', '')} -> R: {final_response}"],
                sources=["CognitiveOrchestrator"],
                types=["memory_interaction"]
            )

        if action == "respond":
            final_result = decision.get("response", "Não consegui formular uma resposta.")

        elif action == "create_agent":
            config = decision.get("new_agent_config") or {}
            agent_name = config.get('agent_name')
            
            if not agent_name or agent_name == "None":
                final_result = f"Erro na criação de agente: {decision.get('response')}"
            else:
                # TASK-09: Auto-creation check
                is_auto = False
                recent_episodes = self.episodic_memory.recall(f"create_agent {agent_name}", top_k=5)
                # Conta quantos pedidos similares nas últimas 24h
                now = datetime.now()
                count = 0
                for ep in recent_episodes:
                    ep_time = datetime.fromisoformat(ep['ts'])
                    if (now - ep_time).total_seconds() < 86400: # 24h
                        count += 1
                
                if count >= 3:
                    is_auto = True
                    print(f"TASK-09: Auto-creation triggered for {agent_name} (frequent demand).")

                print(f"Creating new agent: {agent_name} [TASK-55: Draft Mode]")
                
                # Garantir google_search em especialistas (ou se solicitado)
                tools = config.get('tools', [])
                if "google_search" not in tools:
                    tools.append("google_search") # Default for grounding
                
                new_agent = AgentCore(
                    name=agent_name,
                    purpose=config.get('purpose', 'General Purpose'),
                    system_prompt=config.get('system_prompt'),
                    tools=tools,
                    gcs_client=self.gcs_client
                )
                new_agent.save_to_registry()
                
                # --- TASK-55: QUALITY GATE TRIGGER ---
                # Criar task para o QualityInspector validar o novo agente
                validation_task = {
                    "id": f"AUDIT_{agent_name.upper()}_{os.urandom(2).hex()}",
                    "title": f"Auditoria: Validar DNA de {agent_name}",
                    "type": "tarefa",
                    "responsible": "QualityInspector",
                    "priority": "Alta",
                    "status": "Aberto",
                    "budget_approved": True,
                    "objective": f"Validar se o agente {agent_name} possui conhecimento real sobre seu propósito: {config.get('purpose')}. Se aprovado, mudar status para 'Certified'.",
                    "governance_finops": "Auditoria de qualidade mandatória (TASK-55).",
                    "created_at": datetime.now().isoformat()
                }
                
                if self.gcs_client:
                    reg = self.gcs_client.read_json("demands/registry.json") or {"demands": []}
                    reg['demands'].append(validation_task)
                    self.gcs_client.upload_json(reg, "demands/registry.json")

                final_result = decision.get("response") or f"Agente '{agent_name}' criado e registrado no backlog."
                if is_auto:
                    final_result = "🚀 [AUTO-CREATE] " + final_result
        
        elif action == "update_agent":
            config = decision.get("new_agent_config") or {}
            agent_name = config.get('agent_name')
            if not agent_name: 
                final_result = "Erro: Nome do agente não fornecido para atualização."
            else:
                print(f"Updating agent via Orchestrator: {agent_name}")
                if self.gcs_client:
                    registry = self.gcs_client.read_json("agents/registry.json")
                    for agent in registry.get("agents", []):
                        if agent["agent_name"] == agent_name:
                            if config.get("purpose"): agent["purpose"] = config["purpose"]
                            if config.get("system_prompt"): agent["system_prompt"] = config["system_prompt"]
                            break
                    self.gcs_client.upload_json(registry, "agents/registry.json")
                final_result = decision.get("response") or f"Agente '{agent_name}' atualizado conforme solicitado."

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
                
            final_result = decision.get("response") or f"Demanda TRD '{title}' ({dtype}) registrada com sucesso."

        elif action == "panel_execute":
            panel_agents = decision.get("panel_agents", [])
            task_desc = decision.get("task_description") or user_command
            print(f"Executing PANEL of agents: {panel_agents}")
            
            combined_responses = []
            for agent_name in panel_agents:
                registry = self.gcs_client.read_json("agents/registry.json") if self.gcs_client else None
                agent_config = next((a for a in registry.get("agents", []) if a["agent_name"] == agent_name), None) if registry else None
                
                if agent_config:
                    agent = AgentCore(
                        name=agent_name,
                        purpose=agent_config.get("purpose", ""),
                        system_prompt=agent_config.get("system_prompt", ""),
                        gcs_client=self.gcs_client,
                        finops_manager=self.finops
                    )
                    run_output = agent.run(task_desc)
                    resp = run_output[0] if isinstance(run_output, tuple) else run_output
                    combined_responses.append(f"⚙️ 🤖 **{agent_name}**:\n\n{resp}")
                    # Log individual episodes
                    self.episodic_memory.add(
                        content=f"Parte do Painel: {resp[:150]}",
                        agent=agent_name,
                        tags=["panel_part"]
                    )
                else:
                    combined_responses.append(f"⚠️ Agente '{agent_name}' não localizado para o painel.")
            
            # --- FAPA (Flose Agent Panel Aggregator) ---
            # Depois de coletar as visões individuais, o Orquestrador sintetiza em uma resposta única e fluida
            synthesis_prompt = f"""
            Você é o Orquestrador Cognitivo da Flose AI. 
            Abaixo estão as respostas técnicas de {len(panel_agents)} especialistas sobre a mesma pergunta: "{task_desc}"
            
            RESPOSTAS DO PAINEL:
            {" ".join(combined_responses)}
            
            SUA TAREFA:
            Crie uma resposta ÚNICA, FLUIDA e INTEGRADA. 
            Não use listas. Não use cabeçalhos de nomes de agentes. 
            Faça com que eles "falem na mesma frase", combinando os termos técnicos do UCP com a realidade do Google Merchant Center.
            Limite a resposta a no máximo 5 frases. Linguagem direta e profissional em PT-BR.
            """
            try:
                print("🧠 Sintetizando respostas do painel...")
                synthesis_resp = self.model.generate_content(synthesis_prompt)
                final_result = synthesis_resp.text.strip()
            except Exception as e:
                print(f"Erro na síntese: {e}")
                final_result = "\n\n---\n\n".join(combined_responses)

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
                    gcs_client=self.gcs_client,
                    finops_manager=self.finops
                )
                
                # TASK-23: Memória Compartilhada - Injeção de contexto nas últimas 5 entradas relevantes
                relevant_memories = self.shared_memory.read_relevant(query=task_desc, limit=5)
                context_inject = ""
                if relevant_memories:
                    context_inject = "\n\n--- MEMÓRIA COMPARTILHADA (CONTEXTO ADICIONAL) ---\n"
                    for m in relevant_memories:
                        context_inject += f"- Agente {m['agent']} descobriu sobre '{m['key']}': {m['value']}\n"
                    context_inject += "--- FIM DO CONTEXTO ---\n"
                
                # Execução Real do Especialista
                run_output = agent_obj.run(task_desc + context_inject)
                if isinstance(run_output, tuple):
                    execution_result = run_output[0]
                    # TASK-05: Log usage of the specialized agent
                    if self.finops and hasattr(run_output[1], 'confidence'): # Dummy check to see if evaluation exists
                        # Note: If BaseAgent returned usage_metadata, we could log it here.
                        # For now, we estimate or track it inside the agent if we inject finops there.
                        pass
                else:
                    execution_result = run_output
                
                # Garante que é string antes de formatar
                if not isinstance(execution_result, str):
                    execution_result = str(execution_result)

                # Resposta Composta
                final_result = f"🤖 **{agent_name}**:\n\n{execution_result}"
            else:
                final_result = f"⚠️ Agente '{agent_name}' não encontrado no registro para execução."

        else:
            final_result = decision.get("response", "Decisão não reconhecida.")

        # Persistindo episódio na memória
        user_command = decision.get("user_command", "Unknown")
        self.episodic_memory.add(
            content=f"Usuário: {user_command[:200]} | Ação: {action} | Resultado: {final_result[:150]}",
            agent=decision.get("agent_involved") or "Orchestrator",
            tags=decision.get("knowledge_graph_update", [])
        )
        
        # Ideia 8: BQ Logging
        if bq:
            bq.log_interaction(
                agent=decision.get("agent_involved") or "Orchestrator",
                task=user_command,
                result=final_result,
                cost=decision.get("finops_check", {}).get("estimated_cost_usd", 0)
            )

        # --- TASK-16: Afinidade entre Agentes ---
        current_agent = decision.get("agent_involved")
        if not current_agent and decision.get("panel_agents"):
            current_agent = decision.get("panel_agents")[0]
            
        if current_agent and self.last_agent and current_agent != self.last_agent:
            self._update_affinity(self.last_agent, current_agent)
            
        if current_agent:
            self.last_agent = current_agent

        return final_result

    def _update_affinity(self, agent_a, agent_b):
        """Atualiza a matriz de afinidade entre dois agentes no GCS."""
        if not self.gcs_client: return
        try:
            path = "agents/affinity_matrix.json"
            matrix = self.gcs_client.read_json(path) or {"interactions": {}, "metadata": {"last_update": ""}}
            
            # Key ordenada para ser bidirecional
            pair = tuple(sorted([agent_a, agent_b]))
            pair_key = f"{pair[0]}<->{pair[1]}"
            
            interactions = matrix.get("interactions", {})
            if pair_key not in interactions:
                interactions[pair_key] = {"count": 0, "last_interaction": ""}
            
            interactions[pair_key]["count"] += 1
            interactions[pair_key]["last_interaction"] = datetime.now().isoformat()
            
            matrix["interactions"] = interactions
            matrix["metadata"]["last_update"] = datetime.now().isoformat()
            
            self.gcs_client.upload_json(matrix, path)
        except Exception as e:
            print(f"Erro ao atualizar matriz de afinidade: {e}")

    def run_pipeline(self, agent_names: List[str], initial_prompt: str):
        """Executa uma sequência de agentes onde o output de um alimenta o próximo (TASK-17)."""
        current_input = initial_prompt
        full_results = []
        pipeline_id = f"pipe_{int(time.time())}"
        
        try:
            for i, name in enumerate(agent_names):
                print(f"[PIPELINE] Executing agent {i+1}/{len(agent_names)}: {name}")
                
                # Procura o agente no registro
                agent_data = None
                if self.gcs_client:
                    registry = self.gcs_client.read_json("agents/registry.json")
                    if registry:
                        agent_data = next((a for a in registry.get("agents", []) if a['agent_name'].lower() == name.lower()), None)

                if not agent_data:
                    full_results.append(f"❌ *Agente '{name}' não encontrado.*")
                    continue

                # Instancia e executa
                agent_obj = AgentCore(
                    name=agent_data['agent_name'],
                    purpose=agent_data['purpose'],
                    system_prompt=agent_data['system_prompt'],
                    gcs_client=self.gcs_client,
                    finops_manager=self.finops
                )
                
                # Contexto para o agente saber que está num pipeline
                pipeline_context = f"\n(Você é o passo {i+1} de um pipeline. O input abaixo é o resultado consolidado do passo anterior.)\n"
                
                run_output = agent_obj.run(pipeline_context + current_input)
                resp = run_output[0] if isinstance(run_output, tuple) else run_output
                
                full_results.append(f"🤖 *{agent_data['agent_name']}*:\n{resp}")
                
                # O output do atual vira o input do próximo
                current_input = resp
                
                # Update affinity se houver próximo
                if i < len(agent_names) - 1:
                    next_name = agent_names[i+1]
                    self._update_affinity(agent_data['agent_name'], next_name)

            # Salva o resultado no GCS
            final_json = {
                "pipeline_id": pipeline_id,
                "agents": agent_names,
                "initial_prompt": initial_prompt,
                "steps": full_results,
                "timestamp": datetime.now().isoformat()
            }
            if self.gcs_client:
                self.gcs_client.upload_json(final_json, f"logs/pipelines/{pipeline_id}.json")
            
            return "\n\n---\n\n".join(full_results)
            
        except Exception as e:
            print(f"Erro na pipeline: {e}")
            return f"⚠️ Erro ao executar pipeline: {str(e)}"

    async def run_conselho(self, question: str):
        """Convocação de conselho de especialistas em paralelo (TASK-20)."""
        if not self.gcs_client: return "Erro: GCS Client offline."
        
        try:
            registry = self.gcs_client.read_json("agents/registry.json") or {"agents": []}
            agents_to_call = registry.get("agents", [])[:5] # Limite de 5 para não estourar tokens/limites
            
            async def call_agent_task(agent_data):
                try:
                    agent_obj = AgentCore(
                        name=agent_data['agent_name'],
                        purpose=agent_data['purpose'],
                        system_prompt=agent_data['system_prompt'],
                        gcs_client=self.gcs_client,
                        finops_manager=self.finops
                    )
                    # Força resposta curta de 1 frase
                    short_question = f"{question}\n(RESPONDA EM APENAS 1 FRASE CURTA FOCADA NA SUA ESPECIALIDADE)"
                    run_output = agent_obj.run(short_question)
                    resp = run_output[0] if isinstance(run_output, tuple) else run_output
                    return {"name": agent_data['agent_name'], "response": resp}
                except:
                    return {"name": agent_data['agent_name'], "response": "Não disponível."}

            tasks = [call_agent_task(a) for a in agents_to_call]
            responses = await asyncio.gather(*tasks)
            
            # Síntese Final
            synthesis_prompt = f"""
            Você é o Moderador do Conselho Flose AI. 
            Abaixo estão os conselhos de nossos especialistas sobre: "{question}"
            
            CONSELHOS:
            {json.dumps(responses)}
            
            SUA TAREFA:
            Crie um veredito consolidado. 
            Comece com uma frase de introdução e depois liste as perspectivas de cada agente (1 frase por agente).
            Finalize com uma recomendação final da marca Flose AI.
            Formato: Markdown elegance. Max 10 linhas.
            """
            
            synthesis_resp = self.model.generate_content(synthesis_prompt)
            return synthesis_resp.text.strip()
            
        except Exception as e:
            print(f"Erro no conselho: {e}")
            return f"⚠️ Erro ao convocar conselho: {str(e)}"
