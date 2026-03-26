from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from api.auth import require_auth
from services.agent_service import AgentService
from storage_v3.gcs import GCSClient
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/agents", tags=["Agent Registry"])

# Schemas
class AgentCreate(BaseModel):
    name: str
    purpose: str
    system_prompt: str
    avatar: Optional[str] = None
    tools: Optional[List[str]] = []

class AgentResponse(AgentCreate):
    created_at: Optional[str] = None

# Dependência do Serviço
def get_agent_service(request: Request) -> AgentService:
    bucket = f"flose-ai-platform-{request.app.state.project_id}"
    gcs = GCSClient(bucket)
    return AgentService(gcs)

@router.get("", response_model=List[AgentResponse])
async def list_agents(
    service: AgentService = Depends(get_agent_service),
    admin_email: str = Depends(require_auth)
):
    """Lista todos os agentes ativos no sistema"""
    return await service.list_agents()

@router.post("", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate, 
    service: AgentService = Depends(get_agent_service),
    admin_email: str = Depends(require_auth)
):
    """Cria ou atualiza um agente especializado"""
    try:
        data = agent.model_dump()
        await service.save_agent(data)
        logger.info("agent_saved", name=agent.name)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{name}")
async def delete_agent(
    name: str, 
    service: AgentService = Depends(get_agent_service),
    admin_email: str = Depends(require_auth)
):
    """Remove um agente do registro"""
    success = await service.delete_agent(name)
    if not success:
        raise HTTPException(status_code=404, detail="Agente não encontrado")
    return {"message": f"Agente '{name}' deletado com sucesso!"}
