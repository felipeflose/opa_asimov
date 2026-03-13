import google.generativeai as genai
import json
import os
from PIL import Image
from src.agents.base_agent import BaseAgent
from src.storage.vector_store import VectorStore

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

        DIRETRIZES DE DECISÃO
        - Use 'create_agent' para automações recorrentes.
        - Use 'generate_demand' para novos TRDs (tarefa, reunião, follow-up).
        - Use 'execute' para agentes registrados.
        - Use 'respond' para conhecimento técnico/geral.

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

    def process_command(self, user_command, image_path=None, visual_context=""):
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
            semantic_context = "\n--- MEMÓRIA RECUPERADA (CONTEXTO) ---\n"
            for doc in relevant_docs:
                semantic_context += f"- [{doc['source']}]: {doc['text']}\n"
            semantic_context += "------------------------------------\n"

        prompt = f"""
        Current System Context:
        - GCP Project: {project_id}
        - Region: {region}
        - Telegram Bot: @{tg_bot}
        - FinOps State: {finops_data}
        - Registered Agents: {json.dumps(agents)}
        
        {semantic_context}
        
        {"[VISION AGENT OUTPUT]: " + visual_context if visual_context else ""}
        
        User Command: {user_command}
        {"[IMAGE ATTACHED]" if image_path else ""}
        
        Decision:
        """
        
        content = [self.system_prompt, prompt]
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            content.append(img)
            
        response = self.model.generate_content(content)
        
        # Tracking Real de Custos (FinOps)
        if self.finops and hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            self.finops.log_usage(usage.prompt_token_count, usage.candidates_token_count)
            
        try:
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            decision = json.loads(raw_text)
            return decision
        except Exception as e:
            print(f"Error parsing orchestrator response: {e}")
            return {"error": "Invalid response format", "raw": response.text}

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
            title = demand.get("title", "Nova Demanda")
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
