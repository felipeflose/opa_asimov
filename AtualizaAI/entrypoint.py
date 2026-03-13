import os
import sys
import uvicorn
import asyncio
import subprocess
from fastapi import FastAPI, Request
from fastapi_proxy_lib.core.http import ReverseHttpProxy
from fastapi_proxy_lib.core.tool import ProxyEvent

# --- 1. Inicia o Streamlit em Background ---
print("🚀 Iniciando Streamlit na porta 8081...")
os.environ["STREAMLIT_SERVER_PORT"] = "8081"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"

# NOTA: Usamos cabeçalhos extras para garantir que o Streamlit aceite o tráfego do proxy
subprocess.Popen([
    "streamlit", "run", "src/dashboard/Home.py",
    "--server.port", "8081",
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false",
    "--server.enableXsrfProtection", "false",
    "--server.enableCORS", "false"
])

# --- 2. Setup do Bot (Carregamento Preguiçoso) ---
from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.agents.telegram_agent import TelegramAgent
from src.storage.gcs_client import GCSClient
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
    """Ponto de entrada do Bot: Economiza CPU e R$."""
    data = await request.json()
    agent = await get_tg_agent()
    await agent.process_update(data)
    return {"status": "ok"}

# --- 4. Proxy para o Dashboard Streamlit ---
# O proxy encaminha tudo que não for /telegram_webhook para o localhost:8081
proxy = ReverseHttpProxy("http://127.0.0.1:8081")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def dashboard_proxy(request: Request, path: str):
    return await proxy.proxy(request)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
