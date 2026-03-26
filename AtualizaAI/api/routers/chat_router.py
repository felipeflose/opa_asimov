import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
import structlog
from api.auth import require_auth
from core.orchestrator_v3.orchestrator import OrchestratorV3, InputProcessor, ContextBuilder, DecisionParser, ActionRouter
from core.gemini_client import GeminiClient
from agents_v3.registry import AgentRegistry

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["Orchestrator"])

# Schemas
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None
    image_path: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    metrics: dict
    session_id: str

# Injeção de dependência do orquestrador
# Em produção, carregar do app state via middleware ou singleton
def get_orchestrator(request: Request) -> OrchestratorV3:
    # No BFF v3, usamos as chaves do ambiente carregadas via .env no main.py
    api_key = request.app.state.api_key
    gemini = GeminiClient(api_key=api_key)
    
    return OrchestratorV3(
        input_proc=InputProcessor(),
        context_builder=ContextBuilder(),
        gemini=gemini,
        parser=DecisionParser(),
        router=ActionRouter(agent_registry=AgentRegistry(gemini))
    )

@router.post("", response_model=ChatResponse)
async def process_command(
    req: ChatRequest, 
    admin_email: str = Depends(require_auth),
    orchestrator: OrchestratorV3 = Depends(get_orchestrator)
):
    """Endpoint principal de chat que conversa com o orquestrador"""
    try:
        start_time = time.time()
        logger.info("auth_authorized", user=admin_email)
        
        result = await orchestrator.process_command(
            text=req.message, 
            history=req.history, 
            image_path=req.image_path
        )
        
        # Enriquecimento de resposta v3
        elapsed = time.time() - start_time
        result["metrics"]["latency_sec"] = elapsed
        
        return ChatResponse(
            response=result["message"],
            metrics=result["metrics"],
            session_id=str(int(time.time()))
        )
    except Exception as e:
        logger.error("chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro interno no orquestrador: {str(e)}")
