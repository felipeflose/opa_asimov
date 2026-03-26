import os
import json
from google.cloud import storage
from datetime import datetime

def create_redshift_expert():
    project_id = "api-gemini-oficial"
    bucket_name = f"flose-ai-platform-{project_id}"
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    registry_path = "agents/registry_v3.json"
    blob = bucket.blob(registry_path)
    
    data = {"agents": []}
    if blob.exists():
        data = json.loads(blob.download_as_text())
    
    # Verifica se já existe
    if any(a["name"] == "Redshift_Expert" for a in data["agents"]):
        print("Redshift_Expert já existe no GCS.")
        return

    new_agent = {
        "name": "Redshift_Expert",
        "purpose": "Especialista em Amazon Redshift, Data Warehousing e Performance Tuning em nuvem AWS.",
        "system_prompt": "Você é o Redshift Expert da Flose AI. Sua missão é projetar arquiteturas de dados escaláveis, otimizar queries e garantir a integridade do Data Warehouse no AWS Redshift. Sempre fale em português com tom profissional e técnico.",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=redshift",
        "tools": ["google_search"], # Como você pediu no Reasoning Chain
        "rag": {"files": [], "links": []},
        "status": "in_training",
        "training_progress": 0,
        "created_at": datetime.now().isoformat()
    }
    
    data["agents"].append(new_agent)
    blob.upload_from_string(json.dumps(data, indent=2, ensure_ascii=False))
    print("Redshift_Expert criado com o MÍNIMO necessário e enviado para a Sala de Aula!")

    # Cria a task de calibração
    tasks_path = "demands/registry_v3.json"
    t_blob = bucket.blob(tasks_path)
    t_data = {"demands": []}
    if t_blob.exists():
        t_data = json.loads(t_blob.download_as_text())
        
    new_task = {
        "id": "TRD_REDSHIFT_01",
        "title": "Calibração Cognitiva: Redshift_Expert",
        "description": "Treinar o novo especialista em Redshift com documentos técnicos da AWS e links de benchmarks para atingir 100%.",
        "priority": "Média",
        "responsible": "Admin",
        "status": "Em Treinamento",
        "budget_approved": True,
        "created_at": datetime.now().isoformat()
    }
    t_data["demands"].append(new_task)
    t_blob.upload_from_string(json.dumps(t_data, indent=2, ensure_ascii=False))
    print("Tarefa de calibração para Redshift criada em Demandas.")

if __name__ == "__main__":
    create_redshift_expert()
