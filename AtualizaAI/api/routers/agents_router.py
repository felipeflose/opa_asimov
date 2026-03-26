from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from api.auth import require_auth
from services.agent_service import AgentService
from storage_v3.gcs import GCSClient
import structlog
import uuid

logger = structlog.get_logger()
router = APIRouter(prefix="/api/agents", tags=["Agent Registry"])

class RagConfig(BaseModel):
    files: List[str] = []
    links: List[str] = []

# Schemas
class AgentCreate(BaseModel):
    name: str
    purpose: str
    system_prompt: str
    avatar: Optional[str] = None
    tools: Optional[List[str]] = []
    rag: Optional[RagConfig] = RagConfig()

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

@router.post("/{name}/upload")
async def upload_agent_file(
    name: str,
    file: UploadFile = File(...),
    service: AgentService = Depends(get_agent_service),
    admin_email: str = Depends(require_auth)
):
    """Faz upload de um arquivo para o RAG do agente"""
    try:
        content = await file.read()
        file_path = f"agents/{name}/rag/{uuid.uuid4()}_{file.filename}"
        
        # Upload para o storage
        service.gcs.bucket.blob(file_path).upload_from_string(
            content, content_type=file.content_type
        )
        
        # Atualiza o registro do agente
        agent_list = await service.list_agents()
        for agent in agent_list:
            if agent["name"] == name:
                if "rag" not in agent or agent["rag"] is None:
                    agent["rag"] = {"files": [], "links": []}
                agent["rag"]["files"].append(file_path)
                await service.save_agent(agent)
                break
                
        return {"url": f"gs://{service.gcs.bucket_name}/{file_path}", "filename": file.filename}
    except Exception as e:
        logger.error("agent_upload_error", agent=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/link")
async def add_agent_link(
    name: str,
    link: str = Form(...),
    service: AgentService = Depends(get_agent_service),
    admin_email: str = Depends(require_auth)
):
    """Adiciona um link ao RAG do agente"""
    try:
        agent_list = await service.list_agents()
        for agent in agent_list:
            if agent["name"] == name:
                if "rag" not in agent or agent["rag"] is None:
                    agent["rag"] = {"files": [], "links": []}
                if link not in agent["rag"]["links"]:
                    agent["rag"]["links"].append(link)
                    await service.save_agent(agent)
                break
        return {"message": "Link adicionado com sucesso", "link": link}
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
