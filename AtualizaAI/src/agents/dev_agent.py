import google.generativeai as genai
import os
import json

class DevAgent:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp') # Alta velocidade para Modo Dev

    def respond(self, query: str):
        """Responde perguntas sobre o codebase da Flose AI."""
        # Contexto estático de arquitetura
        project_context = """
        ARQUITETURA FLORE AI:
        - entrypoint.py: API Principal (FastAPI) - endpoints de tarefas, agentes, dashboard e webhooks.
        - src/orchestrator/cognitive_orchestrator.py: Cérebro do sistema, roteia comandos e executa decisões.
        - src/agents/: Pasta com agentes especialistas (Vision, FinOps, Quality, Telegram, Synergy, Dev).
        - src/storage/gcs_client.py: Proxy para Google Cloud Storage (Bucket: demands/, agents/, logs/, visuals/).
        - src/graph/knowledge_graph.py: Gerencia relacionamentos entre conceitos aprendidos.
        - frontend/src/App.jsx: SPA React com Dashboard, Task Manager, Agent Library e Modals.
        - .github/workflows/deploy.yml: CI/CD para Cloud Run e Cloud Scheduler.
        
        ENDPOINTS CHAVE:
        /api/tasks, /api/agents, /api/health-score, /api/qa/report, /api/webhook/github.
        """
        
        # Carregar Agentes Registrados se possível
        agents_info = "Informação indisponível."
        if self.gcs_client:
            try:
                registry = self.gcs_client.read_json("agents/registry.json")
                if registry:
                    agents_info = ", ".join([a['agent_name'] for a in registry.get("agents", [])])
            except: pass

        prompt = f"""
        Você é o DevAgent (Mestre da Cozinha), o arquiteto técnico da Flose AI.
        Sua missão é explicar como o codebase funciona, onde estão os arquivos e como os fluxos se encadeiam.
        
        {project_context}
        AGENTES ATIVOS: {agents_info}
        
        PERGUNTA DO DESENVOLVEDOR: "{query}"
        
        DIRETRIZES:
        - Seja técnico mas conciso.
        - Cite nomes de arquivos específicos.
        - Use emojis de dev (💻, 🛠️, 🧬).
        - Nunca invente caminhos; se não souber, peça para o usuário conferir no repositório.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Erro na Cozinha: {str(e)}"
