import os, json, random
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request

# --- 1. Configurações Globais ---
print("🚀 Iniciando Flose AI Platform com Frontend em React...")

# --- 2. Setup do Bot (Carregamento Preguiçoso) ---
from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.agents.telegram_agent import TelegramAgent
from src.storage.gcs_client import GCSClient
from src.storage.finops_manager import FinOpsManager
from src.graph.knowledge_graph import KnowledgeGraphManager
from src.agents.vision_agent import VisionAgent

app = FastAPI()
API_TOKEN = os.getenv("MASTER_KEY", "fallback_token_change_immediately")

tg_agent = None

async def get_tg_agent():
    global tg_agent
    if tg_agent is None:
        project_id = os.getenv("GCP_PROJECT_ID")
        bucket_name = f"flose-ai-platform-{project_id}"
        gcs = GCSClient(bucket_name, project_id=project_id)
        orchestrator = CognitiveOrchestrator(gcs_client=gcs)
        from src.agents.audio_agent import AudioAgent
        from src.graph.knowledge_graph import KnowledgeGraphManager
        from src.agents.vision_agent import VisionAgent
        
        kg = KnowledgeGraphManager(gcs_client=gcs)
        vision = VisionAgent(gcs_client=gcs)
        audio = AudioAgent(gcs_client=gcs)
        
        tg_agent = TelegramAgent(orchestrator, gcs_client=gcs, kg_manager=kg, vision_agent=vision, audio_agent=audio)
        await tg_agent.setup()
    return tg_agent

def validate_token(request: Request, token: str = None):
    # Tenta pegar do header primeiro (Mais seguro)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if token != API_TOKEN:
        return False
    return True

# --- 3. Endpoint do Webhook do Telegram ---
@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """Acordado pelo Telegram. Custo $0 quando parado."""
    print("📥 Webhook recebido do Telegram!")
    data = await request.json()
    agent = await get_tg_agent()
    print("🤖 Processando update via TelegramAgent...")
    await agent.process_update(data)
    print("✅ Processamento concluído. Retornando 200 OK.")
    return {"status": "ok"}

@app.post("/broker_cycle")
async def broker_cycle():
    """Acionado pelo Cloud Scheduler à meia-noite. Executa o ciclo autônomo."""
    agent = await get_tg_agent()
    
    from src.agents.token_budget_agent import TokenBudgetAgent
    from src.agents.knowledge_broker_agent import KnowledgeBrokerAgent
    
    budget_agent = TokenBudgetAgent(gcs_client=agent.gcs_client)
    agents_allowed = budget_agent.calculate_daily_agent_budget()
    priority_queue = budget_agent.build_priority_queue()
    budget_agent.log_budget_decision(agents_allowed, "Ciclo automático noturno")
    
    broker = KnowledgeBrokerAgent(
        gcs_client=agent.gcs_client,
        orchestrator=agent.orchestrator
    )
    await broker.run_certification_cycle(agent_budget=agents_allowed, priority_queue=priority_queue)
    
    return {"status": "ok", "agents_processed": agents_allowed}

@app.get("/api/broker/status")
async def get_broker_status(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("agents/registry.json") or {"agents": []}
    core_agents = ["FinOpsGuardian", "CognitiveOrchestrator", "VisionAgent", 
                   "AudioAgent", "BriefingAgent", "ReportAgent", 
                   "ProactiveAlertAgent", "EvolutionJob"]
    
    dynamic_agents = [
        a for a in registry.get("agents", []) 
        if a["agent_name"] not in core_agents
    ]
    
    certified = [a for a in dynamic_agents if a.get("certified") == True]
    failed = [a for a in dynamic_agents if a.get("certified") == False]
    pending = [a for a in dynamic_agents if "certified" not in a]
    
    # Buscar último log de ciclo
    last_cycle = None
    try:
        prefix = f"logs/broker/"
        blobs = list(gcs.bucket.list_blobs(prefix=prefix))
        cycle_blobs = [b for b in blobs if "cycle_" in b.name]
        if cycle_blobs:
            cycle_blobs.sort(key=lambda x: x.updated, reverse=True)
            last_cycle = gcs.read_json(
                cycle_blobs[0].name.replace(f"users/{gcs.user_id}/", "") if hasattr(gcs, 'user_id') else cycle_blobs[0].name
            )
    except:
        pass
    
    return {
        "summary": {
            "total_dynamic": len(dynamic_agents),
            "certified": len(certified),
            "failed": len(failed),
            "pending": len(pending)
        },
        "agents": dynamic_agents,
        "last_cycle": last_cycle
    }

@app.post("/daily_briefing")
async def daily_briefing():
    agent = await get_tg_agent()
    from src.agents.briefing_agent import BriefingAgent
    b = BriefingAgent(agent.orchestrator, agent.gcs_client)
    await b.send()
    return {"status": "ok"}

@app.post("/weekly_alerts")
async def weekly_alerts():
    agent = await get_tg_agent()
    from src.agents.proactive_alert import ProactiveAlertAgent
    pa = ProactiveAlertAgent(agent.kg_manager, agent.gcs_client, agent.orchestrator)
    await pa.notify()
    return {"status": "ok"}

@app.post("/evolution_job")
async def evolution_job():
    agent = await get_tg_agent()
    from src.agents.evolution_job import EvolutionJob
    job = EvolutionJob(agent.gcs_client, agent.orchestrator)
    job.run()
    return {"status": "ok"}

@app.post("/weekly_report")
async def weekly_report():
    agent = await get_tg_agent()
    from src.agents.weekly_report_agent import WeeklyReportAgent
    r = WeeklyReportAgent(agent.gcs_client, agent.orchestrator)
    await r.generate_and_send()
    return {"status": "ok"}

@app.post("/api/auth")
async def verify_auth(request: Request):
    data = await request.json()
    client_key = data.get("key")
    master_key = os.getenv("MASTER_KEY")
    if not master_key:
        return {"status": "error", "message": "Secret Manager configuration missing."}
    
    if client_key == master_key:
        return {"status": "authorized", "token": API_TOKEN}
    return {"status": "unauthorized"}

@app.get("/api/stats")
async def get_stats(request: Request, token: str = None):
    # Proteção via header ou fallback token
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
        
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # 1. Pegar FinOps Real
    finops = FinOpsManager(gcs_client=gcs)
    summary = finops.get_daily_summary()
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_data = summary.get(today, {"tokens": 0, "cost": 0.0, "calls": 0})
    
    # 2. Pegar Agentes Reais
    registry_agents = gcs.read_json("agents/registry.json")
    agents_count = len(registry_agents.get("agents", [])) if registry_agents else 0
    
    # 3. Pegar Tasks (Demands) Reais
    registry_tasks = gcs.read_json("demands/registry.json")
    tasks_count = len(registry_tasks.get("demands", [])) if registry_tasks else 0
    
    return {
        "tokens": f"{today_data['tokens']/1000:.1f}k" if today_data['tokens'] > 0 else "0k",
        "cost": f"${today_data.get('total_cost', today_data['cost']):.2f}",
        "tasks": tasks_count,
        "agents": agents_count,
        "calls": today_data["calls"],
        "agent_breakdown": today_data.get("agents", {})
    }

@app.get("/api/dora/summary")
async def get_dora_summary(request: Request, token: str = None):
    """Retorna as métricas DORA formatadas para o Frontend."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    from src.storage.dora_manager import DoraManager
    dora = DoraManager(gcs_client=gcs)
    return dora.get_metrics_summary()

@app.post("/api/dora/incident")
async def report_incident(data: dict, request: Request, token: str = None):
    """Registra uma falha ou incidente para cálculo de MTTR e CFR."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
        
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    from src.storage.dora_manager import DoraManager
    dora = DoraManager(gcs_client=gcs)
    
    dora.log_incident(
        title=data.get("title", "Incidente não detalhado"),
        description=data.get("description", ""),
        severity=data.get("severity", "baixa")
    )
    return {"status": "incident_logged"}

@app.post("/api/webhook/github")
async def github_webhook(request: Request):
    """Recebe webhooks do GitHub para Push e PR merges."""
    # Para validar a origem real em prod, verificar assinatura do payload X-Hub-Signature-256
    
    payload = await request.json()
    action = payload.get("action")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    from src.storage.dora_manager import DoraManager
    dora = DoraManager(gcs_client=gcs)
    
    # Notificação do Telegram
    import asyncio
    agent = await get_tg_agent()
    
    # Se for um Push na main (dispara em cada merge tbm)
    if payload.get("ref") == "refs/heads/main":
        # Logar commits individuais para histórico
        for commit in payload.get("commits", []):
            dora.log_commit(
                commit_hash=commit.get("id"),
                author=commit.get("author", {}).get("name", "Unknown"),
                message=commit.get("message", "")
            )
            
        # LOG DE DEPLOY (A frequência DORA se baseia aqui) usando o SHA final (HEAD)
        final_sha = payload.get("after")
        if final_sha and final_sha != "0000000000000000000000000000000000000000":
            dora.log_deployment(commit_hash=final_sha)
            
            # Avisar no Telegram sobre o Deploy
            msg = f"🚀 *ROBO: Deploy na Main!*\n**SHA**: `{final_sha[:7]}`\nAs métricas DORA foram recalculadas."
            asyncio.create_task(agent.bot.send_message(chat_id=agent.admin_chat_id, text=msg, parse_mode='Markdown'))
            
        return {"status": "commits_and_deploy_logged"}
        
    # Se for PR Merged
    elif "pull_request" in payload and action == "closed" and payload["pull_request"].get("merged"):
        pr = payload["pull_request"]
        merge_commit = pr.get("merge_commit_sha")
        title = pr.get("title")
        user = pr.get("user", {}).get("login")
        
        # Considerando o merge commit como o deploy point
        if merge_commit:
            dora.log_commit(merge_commit, user, title)
            dora.log_deployment(merge_commit)
            
            msg = f"🎉 *Pull Request Merged!*\n**PR**: {title}\n**Merge Hash**: {merge_commit[:7]}\n**Autor**: {user}\nAs métricas DORA foram atualizadas."
            asyncio.create_task(agent.bot.send_message(chat_id=agent.admin_chat_id, text=msg, parse_mode='Markdown'))
            
        return {"status": "pr_merged_logged"}
        
    return {"status": "ignored"}


@app.get("/api/graph")
async def get_graph(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    graph_data = gcs.read_json("knowledge/global_graph.json")
    if not graph_data:
        # Fallback se não existir no GCS
        from src.graph.knowledge_graph import KnowledgeGraphManager
        kg = KnowledgeGraphManager(gcs_client=gcs)
        graph_data = gcs.read_json("knowledge/global_graph.json")
    
    return graph_data or {"nodes": [], "links": []}

@app.get("/api/health-score")
async def get_health_score(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    try:
        score = 0
        # 1. % de tarefas concluídas (Máx 25)
        total_tasks = 0
        completed_tasks = 0
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, "r") as f:
                tasks = json.load(f)
                total_tasks = len(tasks)
                completed_tasks = len([t for t in tasks if t.get("status") in ["Concluído", "COMPLETED", "done"]])
        
        task_score = (completed_tasks / total_tasks * 25) if total_tasks > 0 else 25
        score += task_score
        
        # 2. Custo abaixo do budget (Máx 25)
        budget_score = 25
        if hasattr(orchestrator, 'finops'):
             report = orchestrator.finops.get_finops_report()
             if "Error" in str(report) or "Exeeded" in str(report): 
                 budget_score = 0
        score += budget_score
        
        # 3. Agentes configurados (Máx 25)
        # O orquestrador tem um atributo 'agents' que é um dicionário
        total_agents = len(orchestrator.agents) if hasattr(orchestrator, 'agents') else 0
        ready_agents = 0
        if total_agents > 0:
            for name, agent in orchestrator.agents.items():
                # Verificar se o agente tem uma personalidade ou algo preenchido
                if hasattr(agent, 'personality') and agent.personality:
                    ready_agents += 1
                elif hasattr(agent, 'purpose') and agent.purpose:
                    ready_agents += 1
            agent_score = (ready_agents / total_agents * 25)
        else:
            agent_score = 25
        score += agent_score
        
        # 4. Knowledge Graph (Máx 25)
        kg_score = 0
        graph_data = gcs.read_json("knowledge/global_graph.json")
        if graph_data:
             node_count = len(graph_data.get("nodes", []))
             if node_count >= 10:
                  kg_score = 25
             else:
                  kg_score = (node_count / 10 * 25)
        score += kg_score
        
        return {"score": round(score, 1), "details": {
            "tasks": task_score,
            "budget": budget_score,
            "agents": agent_score,
            "kg": kg_score
        }}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/agents/affinity")
async def get_agent_affinity(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    try:
        matrix = gcs.read_json("agents/affinity_matrix.json")
        return matrix or {"interactions": {}}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/docs")
def get_documentation():
    import os
    try:
        path = os.path.join(os.path.dirname(__file__), "docs", "index.md")
        if not os.path.exists(path):
             return Response(content="# Docs\nFile not found.", media_type="text/markdown")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/markdown")
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/tasks/cleanup")
async def cleanup_tasks(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    import shutil
    import json
    from datetime import datetime
    try:
        if os.path.exists(REGISTRY_PATH):
            backup_path = f"registry_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(REGISTRY_PATH, backup_path)
            with open(REGISTRY_PATH, "w") as f:
                json.dump([], f)
        return {"status": "success", "message": "Backend cleaned and backup created."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/tasks")
async def get_tasks(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("demands/registry.json")
    if not registry or not registry.get("demands"):
        # Gerar alguns dados iniciais se estiver vazio
        initial_tasks = {
            "demands": [
                {
                    "id": "TRD-001", 
                    "title": "Deploy Initial Core", 
                    "status": "COMPLETED", 
                    "priority": "Alta",
                    "objective": "Estabelecer a base sólida da plataforma Flose AI no Google Cloud Run.",
                    "governance_finops": "Custo mensal estimado em $12.00 via Cloud Run scale-to-zero.",
                    "responsible": "SystemAgent"
                },
                {
                    "id": "TRD-002", 
                    "title": "Setup React Dashboard", 
                    "status": "IN_PROGRESS", 
                    "priority": "Alta",
                    "objective": "Criar centro de comando visual para orquestração de agentes.",
                    "governance_finops": "Tráfego de saída (Egress) estimado em 20GB/mês.",
                    "responsible": "FrontendAgent"
                },
                {
                    "id": "TRD-003", 
                    "title": "Integrate Vision Agent", 
                    "status": "Aberto", 
                    "priority": "Média",
                    "objective": "Permitir que a plataforma processe e entenda imagens complexas via Gemini Vision.",
                    "governance_finops": "Custo por imagem estimado em $0.0025.",
                    "responsible": "VisionAgent"
                }
            ]
        }
        gcs.upload_json(initial_tasks, "demands/registry.json")
        return initial_tasks["demands"]
    
    return registry.get("demands", [])

@app.post("/api/tasks/update-status")
async def update_task_status(request: Request, task_id: str, new_status: str = None, new_priority: str = None, token: str = None):
    """Atualiza o status de uma tarefa e aprova o orçamento se movido para 'Em Progresso'."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("demands/registry.json")
    if not registry or "demands" not in registry:
        return {"error": "Registry empty"}
        
    found = False
    for task in registry["demands"]:
        if task["id"] == task_id:
            if new_status:
                task["status"] = new_status
                # Lógica solicitada pelo usuário: Arrastar para a próxima raia = aprovado
                if new_status in ["Em Progresso", "IN_PROGRESS"]:
                    task["budget_approved"] = True
                
                # TASK-14: Se voltar para Aberto, resetar aprovação
                if new_status in ["Aberto", "OPEN"]:
                    task["budget_approved"] = False
            
            if new_priority:
                task["priority"] = new_priority
                
            found = True
            break
            
    if found:
        gcs.upload_json(registry, "demands/registry.json")
        return {"status": "success", "message": f"Task {task_id} updated to {new_status}"}
    
    return {"error": "Task not found"}

@app.post("/api/tasks/audit-finops")
async def audit_finops(task_id: str, request: Request, token: str = None):
    """Usa o LLM para preencher Objective e FinOps de uma tarefa existente que está vazia."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    orchestrator = CognitiveOrchestrator(gcs_client=gcs)
    
    registry = gcs.read_json("demands/registry.json")
    task = next((t for t in registry.get("demands", []) if t["id"] == task_id), None)
    if not task: return {"error": "Task not found"}
    
    prompt = f"""
    Como FinOps Guardian e Auditor de Qualidade, analise esta tarefa:
    Título: {task['title']}
    Responsável: {task.get('responsible')}
    
    Gere:
    1. Um 'objective' detalhado e técnico.
    2. Uma diretriz de 'governance_finops' (custo estimado, infra necessária, regras de economia).
    
    Responda em JSON:
    {{
      "objective": "...",
      "governance_finops": "..."
    }}
    """
    
    res = orchestrator.call_gemini(prompt)
    if "```json" in res: res = res.split("```json")[1].split("```")[0].strip()
    
    try:
        audit_data = json.loads(res)
        task["objective"] = audit_data.get("objective", task.get("objective"))
        task["governance_finops"] = audit_data.get("governance_finops", task.get("governance_finops"))
        gcs.upload_json(registry, "demands/registry.json")
        return {"status": "success", "task": task}
    except:
        return {"error": "Erro no processamento da auditoria IA"}

@app.get("/api/activity")
async def get_activity(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    activity_list = []
    
    try:
        # 1. Executions
        prefix_exec = f"users/{gcs.user_id}/logs/executions/"
        blobs_exec = list(gcs.bucket.list_blobs(prefix=prefix_exec))
        blobs_exec.sort(key=lambda x: x.updated, reverse=True)
        
        for blob in blobs_exec[:10]:
            data = gcs.read_json(blob.name.replace(f"users/{gcs.user_id}/", ""))
            if data:
                activity_list.append({
                    "agent": data.get("agent"),
                    "message": data.get("result"),
                    "timestamp": data.get("timestamp")
                })

        # 2. Telegram
        prefix_tg = f"users/{gcs.user_id}/logs/telegram/"
        blobs_tg = list(gcs.bucket.list_blobs(prefix=prefix_tg))
        blobs_tg.sort(key=lambda x: x.updated, reverse=True)
        
        for blob in blobs_tg[:15]:
            data = gcs.read_json(blob.name.replace(f"users/{gcs.user_id}/", ""))
            if data:
                decision = data.get("decision", {})
                agent = decision.get("agent_involved") or "Orchestrator"
                activity_list.append({
                    "agent": agent,
                    "message": data.get("response") or data.get("user_text"),
                    "timestamp": data.get("timestamp")
                })
    except Exception as e:
        print(f"Error loading activity: {e}")
            
    activity_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return activity_list

@app.get("/api/qa/report")
async def qa_report(request: Request, token: str = None):
    """Quality Inspector: relatório completo de agentes, tarefas e interações."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # Carregar dados
    agents_registry = gcs.read_json("agents/registry.json") or {"agents": []}
    task_registry = gcs.read_json("demands/registry.json") or {"demands": []}
    agents = agents_registry.get("agents", [])
    tasks = task_registry.get("demands", [])
    
    # Carregar todas as interações (executions + telegram)
    all_interactions = []
    try:
        prefix_exec = f"users/{gcs.user_id}/logs/executions/"
        blobs_exec = list(gcs.bucket.list_blobs(prefix=prefix_exec))
        blobs_exec.sort(key=lambda x: x.updated, reverse=True)
        for blob in blobs_exec[:30]:
            data = gcs.read_json(blob.name.replace(f"users/{gcs.user_id}/", ""))
            if data:
                all_interactions.append({
                    "type": "execution",
                    "agent": data.get("agent", "Unknown"),
                    "task_id": data.get("task_id"),
                    "result": data.get("result", ""),
                    "timestamp": data.get("timestamp"),
                    "status": data.get("status", "completed")
                })
        
        prefix_tg = f"users/{gcs.user_id}/logs/telegram/"
        blobs_tg = list(gcs.bucket.list_blobs(prefix=prefix_tg))
        blobs_tg.sort(key=lambda x: x.updated, reverse=True)
        for blob in blobs_tg[:30]:
            data = gcs.read_json(blob.name.replace(f"users/{gcs.user_id}/", ""))
            if data:
                decision = data.get("decision", {})
                agent_name = decision.get("agent_involved") or "Orchestrator"
                all_interactions.append({
                    "type": "telegram",
                    "agent": agent_name,
                    "task_id": decision.get("task_id"),
                    "input": data.get("user_text", ""),
                    "result": data.get("response", ""),
                    "timestamp": data.get("timestamp"),
                    "action": decision.get("action")
                })
    except Exception as e:
        print(f"Error loading QA interactions: {e}")
    
    # Montar relatório por agente
    report = []
    for agent in agents:
        agent_name = agent.get("agent_name", "Unknown")
        
        # Tarefas desse agente
        agent_tasks = [t for t in tasks if t.get("responsible") == agent_name]
        
        # Interações desse agente
        agent_interactions = [i for i in all_interactions if i.get("agent") == agent_name]
        agent_interactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Calcular acertividade
        total_tasks = len(agent_tasks)
        completed = len([t for t in agent_tasks if t.get("status") in ("Concluído", "COMPLETED", "done")])
        open_tasks = len([t for t in agent_tasks if t.get("status") in ("Aberto", "OPEN", "pending")])
        in_progress = len([t for t in agent_tasks if t.get("status") in ("Em Progresso", "IN_PROGRESS")])
        
        # Acertividade: tarefas concluídas / total + bonus por ter prompt definido
        has_prompt = bool(agent.get("system_prompt"))
        has_tools = len(agent.get("tools", [])) > 0
        
        if total_tasks > 0:
            accuracy = round((completed / total_tasks) * 100)
        elif len(agent_interactions) > 0:
            accuracy = 70  # tem atividade mas sem tarefas = aceitável
        else:
            accuracy = 0  # sem tarefas e sem atividade
        
        # Bonus: +10 se tem prompt, +5 se tem tools
        if has_prompt:
            accuracy = min(100, accuracy + 10)
        if has_tools:
            accuracy = min(100, accuracy + 5)
        
        report.append({
            "agent_name": agent_name,
            "purpose": agent.get("purpose", "Sem propósito definido"),
            "has_prompt": has_prompt,
            "has_tools": has_tools,
            "tools": agent.get("tools", []),
            "tasks": agent_tasks,
            "task_summary": {
                "total": total_tasks,
                "completed": completed,
                "open": open_tasks,
                "in_progress": in_progress
            },
            "interactions": agent_interactions[:10],
            "total_interactions": len(agent_interactions),
            "accuracy": accuracy
        })
    
    # Agentes não registrados que aparecem nas interações
    registered_names = {a.get("agent_name") for a in agents}
    orphan_agents = set()
    for i in all_interactions:
        if i.get("agent") and i.get("agent") not in registered_names:
            orphan_agents.add(i.get("agent"))
    
    # Tarefas sem agente atribuído
    unassigned_tasks = [t for t in tasks if not t.get("responsible") or t.get("responsible") not in registered_names]
    
    report.sort(key=lambda x: x["accuracy"])
    
    return {
        "agents": report,
        "orphan_agents": list(orphan_agents),
        "unassigned_tasks": unassigned_tasks,
        "total_interactions": len(all_interactions),
        "summary": {
            "total_agents": len(agents),
            "total_tasks": len(tasks),
            "avg_accuracy": round(sum(a["accuracy"] for a in report) / len(report)) if report else 0
        }
    }

@app.post("/api/qa/enrich-agent")
async def enrich_agent(request: Request, agent_name: str, token: str = None):
    """Quality Inspector: Enriquece propósito, prompt e cria tarefas para o agente."""
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
    orchestrator = CognitiveOrchestrator(gcs_client=gcs)
    
    # 1. Carregar Agente
    agents_reg = gcs.read_json("agents/registry.json") or {"agents": []}
    agent_idx = next((i for i, a in enumerate(agents_reg.get("agents", [])) if a["agent_name"] == agent_name), None)
    if agent_idx is None: return {"error": "Agent not found"}
    agent_data = agents_reg["agents"][agent_idx]
    
    # 2. Carregar Tarefas
    task_reg = gcs.read_json("demands/registry.json") or {"demands": []}
    agent_tasks = [t for t in task_reg.get("demands", []) if t.get("responsible") == agent_name]
    
    # 3. Solicitar enriquecimento ao LLM
    prompt = f"""
    SISTEMA: Você é o Quality Inspector Supremo da plataforma Flose AI.
    AGENTE ALVO: {agent_name}
    
    ESTADO ATUAL:
    - Propósito: {agent_data.get('purpose')}
    - System Prompt: {agent_data.get('system_prompt')}
    - Tarefas: {json.dumps(agent_tasks)}
    
    SUA MISSÃO:
    1. Re-escreva o 'purpose' para ser extremamente profissional, ambicioso e claro (em Português).
    2. Enriqueça o 'system_prompt' com diretrizes avançadas, tom de voz e protocolos de segurança.
    3. Se o agente não possui tarefas de qualidade ou desafiadoras, sugira uma nova 'TRD' de alto valor estratégico.
    ⚠️ IMPORTANTE: Para a nova tarefa, você DEVE gerar um 'objective' detalhado (mínimo 2 frases) e um processo de 'governance_finops' claro (estimativa de custo e regras de uso).

    RESPONDA EXCLUSIVAMENTE NO FORMATO JSON:
    {{
      "new_purpose": "...",
      "new_system_prompt": "...",
      "suggested_task": {{ 
          "title": "...", 
          "priority": "Alta",
          "objective": "...",
          "governance_finops": "..." 
      }} ou null
    }}
    """
    
    raw_response = orchestrator.call_gemini(prompt)
    if "```json" in raw_response:
        raw_response = raw_response.split("```json")[1].split("```")[0].strip()
    
    try:
        enriched = json.loads(raw_response)
        
        # 4. Atualizar Registro
        agent_data["purpose"] = enriched.get("new_purpose", agent_data["purpose"])
        agent_data["system_prompt"] = enriched.get("new_system_prompt", agent_data["system_prompt"])
        gcs.upload_json(agents_reg, "agents/registry.json")
        
        # 5. Criar Tarefa
        msg_task = ""
        if enriched.get("suggested_task"):
            new_id = f"TRD-{random.randint(100, 999)}"
            new_status = "Aberto"
            new_task = {
                "id": new_id,
                "title": enriched["suggested_task"]["title"],
                "status": new_status,
                "priority": enriched["suggested_task"]["priority"],
                "objective": enriched["suggested_task"].get("objective", "Geração pendente..."),
                "governance_finops": enriched["suggested_task"].get("governance_finops", "Aguardando auditoria..."),
                "responsible": agent_name,
                "budget_approved": False
            }
            if "demands" not in task_reg: task_reg["demands"] = []
            task_reg["demands"].append(new_task)
            gcs.upload_json(task_reg, "demands/registry.json")
            msg_task = f" e nova tarefa {new_id} criada"
            
        return {
            "status": "success",
            "message": f"Agente {agent_name} ajustado com sucesso{msg_task}!",
            "changes": enriched
        }
    except Exception as e:
        return {"error": f"Erro no parsing do Inspector: {str(e)}", "raw": raw_response}

@app.post("/api/qa/auto-fix")
async def qa_auto_fix(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
        
    # Lazy load dependencies
    from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    orchestrator = CognitiveOrchestrator(gcs_client=gcs)
    
    # 1. Carregar estado atual para o prompt
    registry = gcs.read_json("demands/registry.json") or {"demands": []}
    agents = gcs.read_json("agents/registry.json") or {"agents": []}
    
    command = f"""
    SISTEMA EM ALERTA: O usuário solicitou uma CORREÇÃO E AUDITORIA GERAL.
    QualityInspector, você deve agir AGORA:
    1. Analise o registry de demandas: {json.dumps(registry.get('demands', [])[:20])}
    2. Liste todos os problemas críticos encontrados (tarefas paradas, backlog vazio, falta de responsáveis).
    3. Para CADA problema encontrado, tome uma ação:
       - Se o backlog de TRDs estiver vazio ou insuficiente para um projeto de IA, use 'GENERATE_DEMAND' para criar as tarefas de 'Arquitetura', 'Segurança' e 'Entrega'.
       - Se houver falha de agente, use 'CREATE_AGENT'.
    4. Seja extremamente detalhado na sua 'response' final, evidenciando o que você corrigiu.
    """
    
    decision = orchestrator.process_command(command)
    result = orchestrator.execute_decision(decision)
    
    # Log da correção na atividade
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "agent": "QualityInspector",
        "message": f"AUTO-FIX EXECUTADO: {result}",
        "type": "qa_fix"
    }
    # Opcional: Salvar no log de telegram para aparecer no feed
    gcs.upload_json({
        "timestamp": datetime.now().isoformat(),
        "user_text": "CORREÇÃO AUTOMÁTICA",
        "decision": decision,
        "response": result
    }, f"logs/telegram/autofix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return {"status": "success", "result": result}

@app.post("/api/tasks/approve")
async def approve_task(task_id: str, request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("demands/registry.json")
    if registry and "demands" in registry:
        for task in registry["demands"]:
            if task["id"] == task_id:
                task["budget_approved"] = True
                break
        gcs.upload_json(registry, "demands/registry.json")
        return {"status": "success", "message": f"Task {task_id} approved."}
    return {"error": "Task not found"}

@app.post("/api/tasks/execute")
async def execute_task(task_id: str, agent_name: str, request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
        
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # 1. Carregar Task
    registry = gcs.read_json("demands/registry.json")
    task = next((t for t in registry.get("demands", []) if t["id"] == task_id), None)
    
    if not task: return {"error": "Task not found"}
    if not task.get("budget_approved"): return {"error": "Budget not approved"}
    
    # 2. Carregar Agente
    agents_reg = gcs.read_json("agents/registry.json")
    agent_data = next((a for a in agents_reg.get("agents", []) if a["agent_name"] == agent_name), None)
    
    if not agent_data: return {"error": "Agent not found"}
    
    # 3. Executar via AgentCore
    from src.agents.base_agent import BaseAgent
    agent_obj = BaseAgent(
        name=agent_data['agent_name'],
        purpose=agent_data['purpose'],
        system_prompt=agent_data['system_prompt'],
        gcs_client=gcs
    )
    
    task_input = f"Tarefa: {task['title']}\nPrioridade: {task['priority']}\nContexto: {task.get('description', 'N/A')}"
    result, evaluation = agent_obj.run(task_input)
    
    # 4. Salvar Resultado
    import os as pyos
    execution_id = f"EX_{pyos.urandom(4).hex()}"
    exec_data = {
        "task_id": task_id,
        "agent": agent_name,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
    gcs.upload_json(exec_data, f"logs/executions/{execution_id}.json")
    
    # 5. Atualizar Registry
    for t in registry["demands"]:
        if t["id"] == task_id:
            t["status"] = "Concluído"
            t["result_id"] = execution_id
            break
    gcs.upload_json(registry, "demands/registry.json")
    
    # 6. Atualiza o Knowledge Graph
    try:
        from src.graph.knowledge_graph import KnowledgeGraphManager
        kg = KnowledgeGraphManager(gcs_client=gcs)
        kg.add_interaction(
            agent_name=agent_name,
            task_name=task['title'],
            outcome={
                "status": "executed",
                "learned_concepts": [task['title']]
            }
        )
    except Exception as e:
        print(f"Erro ao atualizar o grafo cognitivo: {e}")
    
    return {"status": "success", "result": result}

@app.get("/api/tasks/{task_id}/export")
async def export_task_md(task_id: str, request: Request, token: str = None):
    if not validate_token(request, token):
        from fastapi.responses import Response
        return Response(content="Unauthorized", status_code=401)
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("demands/registry.json")
    task = next((t for t in registry.get("demands", []) if t["id"] == task_id), None)
    if not task: return {"error": "Task not found"}
    
    md_content = f"# TRD: {task['title']}\n\n"
    md_content += f"**ID:** {task['id']}\n"
    md_content += f"**Responsável:** {task.get('responsible', 'IA')}\n"
    md_content += f"**Prioridade:** {task.get('priority', 'Normal')}\n"
    md_content += f"**Status:** {task['status']}\n\n"
    md_content += f"## Objetivo\n{task.get('objective', 'N/A')}\n\n"
    md_content += f"## Governança FinOps\n{task.get('governance_finops', 'N/A')}\n\n"
    
    if task.get("result_id"):
        exec_data = gcs.read_json(f"logs/executions/{task['result_id']}.json")
        if exec_data:
            md_content += f"## Entrega Final\n{exec_data.get('result', 'N/A')}\n"
            md_content += f"**Data:** {exec_data.get('timestamp', 'N/A')}\n"

    from fastapi.responses import Response
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=TRD_{task_id}.md"}
    )

@app.get("/api/tasks/delivery/{result_id}")
async def get_delivery(result_id: str, request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    file_path = f"logs/executions/{result_id}.json"
    data = gcs.read_json(file_path)
    if not data:
        # Tenta sem o prefixo caso o gcs_client já adicione algo ou para compatibilidade
        data = gcs.read_json(f"executions/{result_id}.json")
        
    if not data:
        return {"error": f"Artifact {result_id} not found in path {file_path}"}
    return data

@app.post("/api/agents/upload-avatar")
async def upload_agent_avatar(request: Request, agent_name: str, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    form = await request.form()
    file = form.get("file")
    if not file: return {"error": "No file provided"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # 1. Upload para o GCS
    ext = file.filename.split('.')[-1]
    gcs_path = f"agents/avatars/{agent_name.lower()}_{os.urandom(2).hex()}.{ext}"
    content = await file.read()
    
    blob = gcs.bucket.blob(gcs._full_path(gcs_path))
    blob.upload_from_string(content, content_type=file.content_type)
    
    avatar_url = f"https://storage.googleapis.com/{bucket_name}/{gcs._full_path(gcs_path)}"
    
    # 2. Atualizar Registry
    registry = gcs.read_json("agents/registry.json")
    if registry and "agents" in registry:
        for agent in registry["agents"]:
            if agent["agent_name"] == agent_name:
                agent["avatar"] = avatar_url
                break
        gcs.upload_json(registry, "agents/registry.json")
        
    return {"status": "success", "avatar_url": avatar_url}

@app.get("/api/agents")
async def get_agents(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("agents/registry.json")
    return registry.get("agents", []) if registry else []

@app.post("/api/agents/update")
async def update_agent(agent_data: dict, request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    name = agent_data.get("agent_name")
    registry = gcs.read_json("agents/registry.json")
    
    if registry and "agents" in registry:
        for agent in registry["agents"]:
            if agent["agent_name"] == name:
                agent.update({
                    "purpose": agent_data.get("purpose", agent["purpose"]),
                    "system_prompt": agent_data.get("system_prompt", agent["system_prompt"]),
                    "avatar": agent_data.get("avatar", agent.get("avatar"))
                })
                break
        else:
            return {"error": "Agent not found"}
            
        gcs.upload_json(registry, "agents/registry.json")
        return {"status": "success"}
    return {"error": "Registry not found"}

@app.post("/api/agents/chat")
async def chat_agents(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    data = await request.json()
    query = data.get("query")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    orchestrator = CognitiveOrchestrator(gcs_client=gcs)
    # Contexto específico para Agent Library
    decision = orchestrator.process_command(f"[AGENT REGISTRY COMMAND]: {query}")
    response = orchestrator.execute_decision(decision)
    
    return {"response": response}

    return logs

@app.get("/api/marketplace")
async def get_marketplace(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    from src.agents.marketplace import AgentMarketplace
    market = AgentMarketplace(gcs)
    templates = market.list_templates()
    
    # TRD-P05: Enrich templates with curated metadata
    for t in templates:
        name = t.get("name", "").lower()
        if "finops" in name:
            t["description"] = "Guardião especializado em otimização de custos GCP e FinOps."
            t["use_cases"] = ["Redução de custos", "Análise de faturamento", "Previsão de gastos"]
            t["category"] = "Gêrencia de Cloud"
        elif "task" in name:
            t["description"] = "Gerenciador autônomo de tarefas e demandas TRD."
            t["use_cases"] = ["Organização de backlog", "Track de progresso", "Kanban Automático"]
            t["category"] = "Productivity"
        else:
            t["description"] = t.get("purpose", "Agente especialista customizado.")
            t["use_cases"] = ["Automação de processos", "Análise de dados"]
            t["category"] = "General"
            
    return templates

@app.post("/api/marketplace/export/{agent_name}")
async def export_to_marketplace(agent_name: str, request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    from src.agents.marketplace import AgentMarketplace
    market = AgentMarketplace(gcs)
    res = await market.export_agent(agent_name)
    if res:
        return {"status": "success", "message": f"Agent {agent_name} exported to marketplace."}
    return {"error": "Failed to export agent"}

@app.post("/api/marketplace/import")
async def import_from_marketplace(request: Request, token: str = None):
    if not validate_token(request, token):
        return {"error": "Unauthorized"}
    
    data = await request.json()
    template_name = data.get("template_name")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # Busca o template no GCS
    template_path = f"marketplace/templates/{template_name.lower()}_template.json"
    template_data = gcs.read_json(template_path)
    
    if not template_data:
        return {"error": "Template not found"}

    # Cria novo agente a partir do template
    from src.agents.base_agent import BaseAgent
    new_agent = BaseAgent(
        name=template_data["name"],
        purpose=template_data["purpose"],
        system_prompt=template_data["system_prompt"],
        gcs_client=gcs
    )
    new_agent.save_to_registry()
    
    return {"status": "success", "message": f"Agent {template_data['name']} imported from marketplace."}

@app.get("/api/marketplace/visual-proxy")
async def napkin_visual_proxy(request: Request, url: str = None, token: str = None):
    """
    Proxy autenticado para servir imagens SVG do Napkin AI.
    O browser não pode acessar a URL do Napkin diretamente (precisa de Bearer token).
    Este endpoint baixa e re-serve o SVG com os headers corretos.
    """
    from fastapi.responses import Response
    if not validate_token(request, token):
        return Response(content="Unauthorized", status_code=401)
    if not url:
        return Response(content="Missing url param", status_code=400)
    
    napkin_key = os.getenv("NAPKIN_API_KEY")
    if not napkin_key:
        return Response(content="Napkin key not configured", status_code=500)
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers={
                "Authorization": f"Bearer {napkin_key}",
                "Accept": "image/svg+xml,image/png,*/*"
            })
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/svg+xml")
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Cache-Control": "public, max-age=3600"}
                )
            return Response(content=f"Napkin returned {resp.status_code}", status_code=resp.status_code)
    except Exception as e:
        return Response(content=str(e), status_code=500)

# --- 4. Servir Frontend React ---
# Montamos a pasta dist gerada pelo build do Vite
frontend_path = os.path.join(os.getcwd(), "frontend", "dist")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    async def root_fallback():
        return {"error": "Frontend build not found. Please run 'npm run build' inside frontend directory."}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("entrypoint:app", host="0.0.0.0", port=port, reload=True)
