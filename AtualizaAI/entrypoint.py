import os
import sys
import uvicorn
import asyncio
import subprocess
from fastapi import FastAPI, Request
from starlette_proxy import ProxyMiddleware

# --- 1. Inicia o Streamlit em Background ---
print("🚀 Iniciando Streamlit na porta 8081...")
os.environ["STREAMLIT_SERVER_PORT"] = "8081"
os.environ["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"

subprocess.Popen([
    "streamlit", "run", "src/dashboard/Home.py",
    "--server.port", "8081",
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false",
    "--server.enableXsrfProtection", "false"
])

# --- 2. Setup do Bot (Carregamento Preguiçoso) ---
from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.agents.telegram_agent import TelegramAgent
from src.storage.gcs_client import GCSClient
from src.graph.knowledge_graph import KnowledgeGraphManager
from src.agents.vision_agent import VisionAgent

app = FastAPI()

# Middleware de Proxy para o Streamlit (Trata WebSockets e Estáticos)
app.add_middleware(ProxyMiddleware, upstream="http://127.0.0.1:8081")

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
# Este endpoint PRECISA ser verificado antes do Proxy
@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """Acordado pelo Telegram. Custo $0 quando parado."""
    data = await request.json()
    agent = await get_tg_agent()
    await agent.process_update(data)
    return {"status": "ok"}

# Rota de Health Check
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    # O Uvicorn roda na 8080 recebendo tudo
    uvicorn.run(app, host="0.0.0.0", port=port)
