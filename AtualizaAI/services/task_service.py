from typing import List, Optional, Dict
from storage_v3.gcs import GCSClient
import structlog
import uuid
from datetime import datetime

logger = structlog.get_logger()

class TaskService:
    """Serviço de Domínio para gerenciar demandas (Tasks/TRDs) em GCS"""
    def __init__(self, gcs: GCSClient):
        self.gcs = gcs
        self.registry_path = "demands/registry_v3.json"

    async def list_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """Retorna todas as tarefas registradas"""
        data = self.gcs.get_json(self.registry_path)
        if not data or "demands" not in data:
            return []
        
        tasks = data["demands"]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
            
        return tasks

    async def create_task(self, title: str, description: str, priority: str, responsible: str) -> Dict:
        """Cria uma nova tarefa com id único"""
        task = {
            "id": f"TRD_{uuid.uuid4().hex[:8].upper()}",
            "title": title,
            "description": description,
            "priority": priority,
            "responsible": responsible,
            "status": "Aberto",
            "budget_approved": False,
            "created_at": datetime.now().isoformat()
        }
        
        registry = self.gcs.get_json(self.registry_path) or {"demands": []}
        registry["demands"].append(task)
        
        self.gcs.upload_json(registry, self.registry_path)
        logger.info("task_created", id=task["id"])
        return task

    async def update_status(self, task_id: str, new_status: str) -> bool:
        """Atualiza o status de uma tarefa"""
        registry = self.gcs.get_json(self.registry_path)
        if not registry: return False
        
        found = False
        for i, t in enumerate(registry["demands"]):
            if t["id"] == task_id:
                registry["demands"][i]["status"] = new_status
                found = True
                break
        
        if found:
            return self.gcs.upload_json(registry, self.registry_path)
        return False
