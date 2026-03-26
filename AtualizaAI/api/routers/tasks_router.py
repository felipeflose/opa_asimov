from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from api.auth import require_auth
from services.task_service import TaskService
from storage_v3.gcs import GCSClient
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/tasks", tags=["Task Kanban"])

# Schemas
class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str = "Média"  # "Baixa", "Média", "Alta"
    responsible: str = "Admin"

class TaskResponse(TaskCreate):
    id: str
    status: str
    budget_approved: bool
    created_at: str

# Dependência do Serviço
def get_task_service(request: Request) -> TaskService:
    bucket = f"flose-ai-platform-{request.app.state.project_id}"
    gcs = GCSClient(bucket)
    return TaskService(gcs)

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    service: TaskService = Depends(get_task_service),
    admin_email: str = Depends(require_auth)
):
    """Lista todas as tarefas filtradas opcionalmente por status"""
    return await service.list_tasks(status)

@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate, 
    service: TaskService = Depends(get_task_service),
    admin_email: str = Depends(require_auth)
):
    """Cria uma nova tarefa no backlog"""
    try:
        new_task = await service.create_task(
            title=task.title,
            description=task.description,
            priority=task.priority,
            responsible=task.responsible
        )
        return new_task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str, 
    new_status: str, 
    service: TaskService = Depends(get_task_service),
    admin_email: str = Depends(require_auth)
):
    """Atualiza o status de uma tarefa"""
    success = await service.update_status(task_id, new_status)
    if not success:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return {"message": f"Status da tarefa {task_id} atualizado para {new_status}"}
