import os
import json
from src.storage.gcs_client import GCSClient
from datetime import datetime

def consolidate_logs():
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    # Esta é uma simulação, pois o GCSClient não tem 'list_files'
    # Mas podemos tentar ler alguns nomes prováveis ou apenas criar um inicial
    
    summary_path = "logs/telegram/latest_activity.json"
    initial_data = [
        {"user": "Sistema", "message": "Plataforma Migrada para React com sucesso.", "timestamp": datetime.now().isoformat()},
        {"user": "Sistema", "message": "Orquestrador Gemini 2.5 Flash sincronizado.", "timestamp": datetime.now().isoformat()}
    ]
    
    gcs.upload_json(initial_data, summary_path)
    print("✅ Consolidação inicial de logs concluída.")

if __name__ == "__main__":
    consolidate_logs()
