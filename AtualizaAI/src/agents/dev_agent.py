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
        # TASK-26: Atalho para logs de erro
        if "logs" in query.lower():
            return self.get_error_logs()
        
        # TASK-27: Explorar fluxo de rota
        if "rota" in query.lower():
            return self.explain_route(query)

        # TASK-28: Raio-X de Agente
        if "agente " in query.lower():
            return self.agent_raio_x(query)

        # TASK-29: Diff Diário
        if "diff" in query.lower():
            return self.get_daily_diff()
            
        # TASK-30: Custo por Agente
        if "custo" in query.lower():
            return self.get_agent_cost(query)
            
        # TASK-31: Testar Endpoint
        if "endpoint " in query.lower():
            return self.test_endpoint(query)

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

    def get_error_logs(self):
        """Busca os últimos 20 logs de execução e filtra erros (TASK-26)."""
        if not self.gcs_client: return "GCS Client indisponível."
        try:
            prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
            blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix, max_results=50))
            if not blobs: return "Nenhum log de execução encontrado."
            
            # Ordenar por data decoescente
            blobs.sort(key=lambda x: x.updated, reverse=True)
            
            error_list = []
            for blob in blobs[:20]:
                data = self.gcs_client.read_json(blob.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                if data and ("error" in data or data.get("status") == "error"):
                    ts = data.get("timestamp", "N/A")[11:16]
                    agent = data.get("agent", "Unknown")
                    err_msg = data.get("error") or data.get("message") or "Erro não detalhado"
                    error_list.append(f"⏱️ {ts} | 🤖 {agent} | ❌ {err_msg[:100]}")
            
            if not error_list:
                return "✅ Nenhum erro crítico encontrado nos últimos 20 logs de execução."
            
            header = "🚨 **Últimos Erros Detectados na Cozinha:**\n\n"
            return header + "\n".join(error_list)
        except Exception as e:
            return f"⚠️ Falha ao ler logs no GCS: {e}"

    def explain_route(self, query: str):
        """Explica por quais arquivos e métodos uma mensagem passa (TASK-27)."""
        prompt = f"""
        Você é o DevAgent da Flose AI. Explique passo a passo o FLUXO TÉCNICO de uma mensagem na plataforma 
        baseando-se na ARQUITETURA abaixo:
        
        - telegram_agent.py (setup_webhook -> process_update -> message_handler)
        - vision_agent.py (analyze_image) e audio_agent.py (transcribe)
        - cognitive_orchestrator.py (process_command -> execute_decision)
        - base_agent.py (Agentes especialistas reais)
        - gcs_client.py (Persistência em Bucket)
        - entrypoint.py (API e Webhooks que recebem os gatilhos externos)
        
        PERGUNTA SOBRE A ROTA: "{query}"
        
        Sua resposta deve ser uma lista numerada ou um diagrama Mermaid simplificado (texto) 
        explicando quais métodos de quais arquivos são chamados e em qual ordem.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ Erro ao traçar rota: {str(e)}"

    def agent_raio_x(self, query: str):
        """Extrai raio-x completo de um agente do registry e logs (TASK-28)."""
        if not self.gcs_client: return "GCS Client indisponível."
        try:
            agent_name = query.lower().replace("agente ", "").strip()
            registry = self.gcs_client.read_json("agents/registry.json") or {"agents": []}
            agent_data = next((a for a in registry.get("agents", []) if a['agent_name'].lower() == agent_name), None)
            
            if not agent_data:
                return f"🔍 Agente '{agent_name}' não encontrado no registro oficial."
            
            # Buscar última execução
            prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
            blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix))
            agent_logs = []
            for b in blobs:
                data = self.gcs_client.read_json(b.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                if data and data.get("agent", "").lower() == agent_name:
                    agent_logs.append(data)
            
            agent_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            last_exec = agent_logs[0] if agent_logs else None
            
            info = (
                f"🧬 **RAIO-X: {agent_data['agent_name']}**\n\n"
                f"📝 **System Prompt:** `{agent_data.get('system_prompt', 'N/A')[:150]}...`\n"
                f"🛠️ **Tools:** {', '.join(agent_data.get('tools', [])) or 'Nenhuma'}\n"
                f"📊 **Total de Execuções:** {len(agent_logs)}\n"
            )
            
            if last_exec:
                ts = last_exec.get("timestamp", "N/A")[11:16]
                res = last_exec.get("result", "Sem resultado")[:100].replace("\n", " ")
                info += f"⏱️ **Última Execução ({ts}):** {res}...\n"
            
            return info
        except Exception as e:
            return f"❌ Erro no Raio-X: {e}"

    def get_daily_diff(self):
        """Resume o que mudou no sistema nas últimas 24h (TASK-29)."""
        if not self.gcs_client: return "GCS Client indisponível."
        from datetime import datetime, timedelta
        
        try:
            last_24h = datetime.now() - timedelta(hours=24)
            prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
            blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix))
            
            recent_logs = []
            for b in blobs:
                if b.updated.replace(tzinfo=None) > last_24h:
                    data = self.gcs_client.read_json(b.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                    if data: recent_logs.append(data)

            if not recent_logs:
                return "😴 Nenhuma atividade letárgica nas últimas 24h. Tudo calmo na Flose AI."

            # Analisar logs
            new_tasks = [l for l in recent_logs if l.get("type") == "demand_gen" or "demand_info" in l]
            errors = [l for l in recent_logs if "error" in l or l.get("status") == "error"]
            agents_used = sorted(list(set([l.get("agent", "Orchestrator") for l in recent_logs])))
            
            summary = (
                f"📅 **Resumo das últimas 24h (Changelog):**\n\n"
                f"✅ **Atividade:** {len(recent_logs)} interações processadas.\n"
                f"🤖 **Agentes ativos:** {', '.join(agents_used)}\n"
                f"📝 **Novas Demandas:** {len(new_tasks)}\n"
                f"❌ **Erros Detectados:** {len(errors)}\n\n"
                f"🔗 Use `/cozinha logs` para ver os erros em detalhe."
            )
            return summary
        except Exception as e:
            return f"❌ Erro ao gerar diff: {e}"

    def get_agent_cost(self, query: str):
        """Calcula custo de um agente específico ou geral (TASK-30)."""
        if not self.gcs_client: return "GCS Client indisponível."
        try:
            agent_target = query.lower().replace("custo", "").strip()
            
            # Carregar logs de execução recentes
            prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
            blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix, max_results=100))
            
            total_cost = 0.0
            total_tokens = 0
            count = 0
            
            for b in blobs:
                data = self.gcs_client.read_json(b.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                if not data: continue
                
                # Filtro por agente se especificado
                if agent_target and data.get("agent", "").lower() != agent_target:
                    continue
                
                # Acumula
                total_cost += data.get("cost", 0)
                total_tokens += data.get("tokens", 0)
                count += 1
            
            target_name = agent_target.upper() if agent_target else "TODOS OS AGENTES"
            report = (
                f"💰 **Relatório FinOps: {target_name}**\n\n"
                f"💵 **Custo Estimado (GCP):** ${total_cost:.4f} USD\n"
                f"🧬 **Tokens Consumidos:** {total_tokens:,}\n"
                f"⚙️ **Número de Execuções:** {count}\n"
            )
            return report
        except Exception as e:
            return f"❌ Erro ao calcular custo: {e}"

    def test_endpoint(self, query: str):
        """Testa um endpoint local e retorna o resultado (TASK-31)."""
        import httpx
        import time
        endpoint = query.lower().replace("endpoint", "").strip()
        if endpoint.startswith("/"): endpoint = endpoint[1:]
        
        url = f"http://localhost:8080/api/{endpoint}"
        master_key = os.getenv("MASTER_KEY", "flose-dev-key")
        
        start_time = time.time()
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url, params={"token": master_key})
                elapsed = int((time.time() - start_time) * 1000)
                
                status_emoji = "✅" if r.status_code == 200 else "⚠️"
                res_text = r.text[:200]
                
                return (
                    f"🔌 **Teste de Endpoint: /api/{endpoint}**\n\n"
                    f"{status_emoji} **Status:** {r.status_code}\n"
                    f"⏱️ **Latência:** {elapsed}ms\n"
                    f"📦 **Resposta:** `{res_text}...`"
                )
        except Exception as e:
            return f"❌ Falha ao conectar em {url}: {e}"
