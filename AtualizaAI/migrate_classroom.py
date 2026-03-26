import os
import json
import uuid
from datetime import datetime
from google.cloud import storage

def migrate_classroom():
    project_id = "api-gemini-oficial"
    bucket_name = f"flose-ai-platform-{project_id}"
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # 1. Reset Agents
    registry_path = "agents/registry_v3.json"
    blob = bucket.blob(registry_path)
    
    if blob.exists():
        data = json.loads(blob.download_as_text())
        new_agents = []
        training_count = 0
        
        for agent in data.get("agents", []):
            name = agent.get("name", "")
            # Agentes especialistas fixos no código não entram na sala de aula
            specialists = ["TelegramAgent", "VisionAgent", "FinOpsGuardian", "SystemArchitectAgent"]
            
            # Se não tem RAG e não tem Ferramentas, vai para a Sala de Aula
            has_rag = agent.get("rag") and (agent["rag"].get("files") or agent["rag"].get("links"))
            has_tools = agent.get("tools") and len(agent["tools"]) > 0
            
            if name not in specialists and not has_rag and not has_tools:
                agent["status"] = "in_training"
                agent["training_progress"] = 0
                training_count += 1
            else:
                agent["status"] = "ready"
                agent["training_progress"] = 100
            
            new_agents.append(agent)
            
        data["agents"] = new_agents
        blob.upload_from_string(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"Migração de Agentes concluída: {training_count} enviados para Sala de Aula.")

    # 2. Reset Tasks
    tasks_path = "demands/registry_v3.json"
    tasks_blob = bucket.blob(tasks_path)
    
    new_tasks = []
    # Cria uma task de calibração para cada agente em treinamento
    if blob.exists():
        data = json.loads(blob.download_as_text())
        for agent in data.get("agents", []):
            if agent.get("status") == "in_training":
                task = {
                    "id": f"TRD_{uuid.uuid4().hex[:8].upper()}",
                    "title": f"Calibração Cognitiva: {agent['name']}",
                    "description": f"Treinar o agente {agent['name']} adicionando documentos no RAG e ativando as ferramentas necessárias até atingir 100%.",
                    "priority": "Alta",
                    "responsible": "Admin",
                    "status": "Em Treinamento",
                    "budget_approved": True,
                    "created_at": datetime.now().isoformat()
                }
                new_tasks.append(task)
    
    tasks_blob.upload_from_string(json.dumps({"demands": new_tasks}, indent=2, ensure_ascii=False))
    print(f"Tarefas resetadas: {len(new_tasks)} novas demandas de calibração criadas.")

if __name__ == "__main__":
    migrate_classroom()
