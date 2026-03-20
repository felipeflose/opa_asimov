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
        2. PANEL_EXECUTE: Use quando o tema exigir a visão combinada de DOIS ou TRÊS especialistas (ex: Merchant Center + UCP). Requer o campo "panel_agents" com a lista de nomes.
        3. CREATE_AGENT: Crie novos especialistas se o tema for inédito.
        4. UPDATE_AGENT: Modifique o propósito ou o prompt de um agente existente.
        5. GENERATE_DEMAND: Use para registrar novas TRDs no Kanban.
        6. RESPOND: Interações simples ou respostas sobre agendamento/status.

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

    def process_command(self, user_command, image_path=None, visual_context="", chat_history=None):
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
        
        if action in ["execute", "generate_demand"] and infra_cost > 1.0:
            try:
                from src.agents.debate_agent import DebateAgent
                debate_sys = DebateAgent()
                result = debate_sys.debate(
                    question=decision.get("task_description") or decision.get("response"),
                    context=decision.get("reasoning", "")
                )
                if result["verdict"].get("decision") == "abort":
                    return f"⚖️ **Debate Agent bloqueou a ação.**\n\nMotivo: {result['verdict']['reasoning']}"
            except Exception as e:
                print(f"Erro no debate: {e}")

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
                        gcs_client=self.gcs_client
                    )
                    resp = agent.execute(task_desc)
                    combined_responses.append(f"⚙️ 🤖 **{agent_name}**:\n\n{resp}")
                    # Log individual episodes
                    self.episodic_memory.store(agent_name, resp, {"action": "panel_part"})
                else:
                    combined_responses.append(f"⚠️ Agente '{agent_name}' não localizado para o painel.")
            
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

        return final_result
