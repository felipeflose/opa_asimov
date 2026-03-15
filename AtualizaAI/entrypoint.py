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

@app.post("/api/auth")
async def verify_auth(request: Request):
    data = await request.json()
    client_key = data.get("key")
    master_key = os.getenv("MASTER_KEY", "flosetec")
    
    if client_key == master_key:
        return {"status": "authorized", "token": "flosetoken_secure_v2"}
    return {"status": "unauthorized"}

@app.get("/api/stats")
async def get_stats(token: str = None):
    # Proteção simples via token
    if token != "flosetoken_secure_v2":
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
        "cost": f"${today_data['cost']:.2f}",
        "tasks": tasks_count,
        "agents": agents_count,
        "calls": today_data["calls"]
    }

@app.get("/api/graph")
async def get_graph(token: str = None):
    if token != "flosetoken_secure_v2":
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
    if token != "flosetoken_secure_v2":
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

@app.post("/api/tasks/approve")
async def approve_task(task_id: str, token: str = None):
    if token != "flosetoken_secure_v2":
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
    if token != "flosetoken_secure_v2":
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
    result = agent_obj.run(task_input)
    
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
    
    return {"status": "success", "result": result}

@app.get("/api/tasks/delivery/{result_id}")
async def get_delivery(result_id: str, token: str = None):
    if token != "flosetoken_secure_v2":
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    data = gcs.read_json(f"logs/executions/{result_id}.json")
    return data or {"error": "Result not found"}

@app.get("/api/agents")
async def get_agents(token: str = None):
    if token != "flosetoken_secure_v2":
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    registry = gcs.read_json("agents/registry.json")
    return registry.get("agents", []) if registry else []

@app.post("/api/agents/update")
async def update_agent(agent_data: dict, token: str = None):
    if token != "flosetoken_secure_v2":
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
    if token != "flosetoken_secure_v2":
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

@app.get("/api/activity")
async def get_activity(token: str = None):
    if token != "flosetoken_secure_v2":
        return {"error": "Unauthorized"}
    
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # Listar últimos logs de telegram (prefixo logs/telegram/)
    # Como não temos um list_files eficiente aqui, vamos tentar ler os últimos 5 logs 
    # se tivéssemos uma forma de listar. O GCSClient precisa de um list_files.
    
    # Por enquanto, vamos retornar uma mensagem amigável ou tentar implementar um mini-list no gcs
    logs = gcs.read_json("logs/telegram/latest_activity.json")
    if not logs:
        # Se não houver o sumário, retornamos um vazio
        return []
    
    return logs

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
