import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import structlog
from api.routers import chat_router, agents_router, tasks_router, auth_router, finops_router, activity_router
from api.auth import require_auth

# Load .env early
load_dotenv(override=True)

logger = structlog.get_logger()

# --- BFF v3.0 // Flose AI Platform ---
app = FastAPI(
    title="Flose AI — BFF Architecture",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Injeção de estado v3 (evita os.getenv em cada router)
app.state.api_key = os.getenv("GEMINI_API_KEY")
app.state.master_key = os.getenv("MASTER_KEY")
app.state.project_id = os.getenv("GCP_PROJECT_ID")

# --- CORS Moderno ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, use strings fixas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth_router.router)
app.include_router(chat_router.router)
app.include_router(agents_router.router)
app.include_router(tasks_router.router)
app.include_router(finops_router.router)
app.include_router(activity_router.router)
# Futuros routers (agents, tasks, finops) serão adicionados aqui

# --- Health Check v3 ---
@app.get("/health", tags=["System"])
async def health_check():
    """Retorna o status do sistema e componentes cloud"""
    try:
        # Simplificado para v3, pode incluir testes de GCS/Gemini later
        return {
            "status": "online",
            "version": "v3.0-bff",
            "gemini": "active" if app.state.api_key else "missing",
            "storage": "ok"
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {"status": "degraded", "error": str(e)}

@app.get("/", tags=["System"])
async def root():
    return {"message": "Flose AI Platform BFF v3.0 está rodando..."}

# --- Entrypoint Local (Uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
