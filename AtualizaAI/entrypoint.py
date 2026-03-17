import os
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
        kg = KnowledgeGraphManager(gcs_client=gcs)
        vision = VisionAgent(gcs_client=gcs)
        tg_agent = TelegramAgent(orchestrator, gcs_client=gcs, kg_manager=kg, vision_agent=vision)
        await tg_agent.setup()
    return tg_agent

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
    from src.agents.report_agent import ReportAgent
    r = ReportAgent(agent.gcs_client, agent.orchestrator)
    await r.send_to_telegram()
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
async def get_stats(token: str = None):
    # Proteção simples via token
    if token != API_TOKEN:
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
        "calls": today_data["calls"]
    }

@app.get("/api/graph")
async def get_graph(token: str = None):
    if token != API_TOKEN:
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

@app.get("/api/tasks")
async def get_tasks(token: str = None):
    if token != API_TOKEN:
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("demands/registry.json")
    if not registry or not registry.get("demands"):
        # Gerar alguns dados iniciais se estiver vazio
        initial_tasks = {
            "demands": [
                {"id": "TRD-001", "title": "Deploy Initial Core", "status": "COMPLETED", "priority": "Alta"},
                {"id": "TRD-002", "title": "Setup React Dashboard", "status": "IN_PROGRESS", "priority": "Alta"},
                {"id": "TRD-003", "title": "Integrate Vision Agent", "status": "Aberto", "priority": "Média"}
            ]
        }
        gcs.upload_json(initial_tasks, "demands/registry.json")
        return initial_tasks["demands"]
    
    return registry.get("demands", [])

@app.get("/api/activity")
async def get_activity(token: str = None):
    if token != API_TOKEN:
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

@app.post("/api/qa/auto-fix")
async def qa_auto_fix(token: str = None):
    if token != API_TOKEN:
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
async def approve_task(task_id: str, token: str = None):
    if token != API_TOKEN:
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
async def execute_task(task_id: str, agent_name: str, token: str = None):
    if token != API_TOKEN:
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

@app.get("/api/tasks/delivery/{result_id}")
async def get_delivery(result_id: str, token: str = None):
    if token != API_TOKEN:
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    file_path = f"logs/executions/{result_id}.json"
    data = gcs.read_json(file_path)
    if not data:
        return {"error": f"Artifact {result_id} not found in path {file_path}"}
    return data

@app.get("/api/agents")
async def get_agents(token: str = None):
    if token != API_TOKEN:
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("agents/registry.json")
    return registry.get("agents", []) if registry else []

@app.post("/api/agents/update")
async def update_agent(agent_data: dict, token: str = None):
    if token != API_TOKEN:
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
    if token != API_TOKEN:
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
async def get_marketplace(token: str = None):
    if token != API_TOKEN:
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    from src.agents.marketplace import AgentMarketplace
    market = AgentMarketplace(gcs)
    return market.list_templates()

@app.post("/api/marketplace/export/{agent_name}")
async def export_to_marketplace(agent_name: str, token: str = None):
    if token != API_TOKEN:
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
    if token != API_TOKEN:
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
async def napkin_visual_proxy(url: str = None, token: str = None):
    """
    Proxy autenticado para servir imagens SVG do Napkin AI.
    O browser não pode acessar a URL do Napkin diretamente (precisa de Bearer token).
    Este endpoint baixa e re-serve o SVG com os headers corretos.
    """
    from fastapi.responses import Response
    if token != API_TOKEN:
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
