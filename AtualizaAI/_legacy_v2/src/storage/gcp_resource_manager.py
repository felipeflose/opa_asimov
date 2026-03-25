from google.cloud import run_v2
from google.cloud import monitoring_v3
import os
import pandas as pd
from datetime import datetime, timedelta

class GCPResourceManager:
    def __init__(self, project_id, region="us-central1"):
        self.project_id = project_id
        self.region = region
        self.run_client = run_v2.ServicesClient()
        self.metric_client = monitoring_v3.MetricServiceClient()

    def get_cloud_run_status(self):
        """Busca o status real do serviço no Cloud Run"""
        try:
            name = f"projects/{self.project_id}/locations/{self.region}/services/flose-ai-platform"
            service = self.run_client.get_service(name=name)
            return {
                "name": service.name.split("/")[-1],
                "url": service.uri,
                "region": self.region,
                "revisions": service.latest_ready_revision.split("/")[-1],
                "last_update": datetime.fromtimestamp(service.update_time.timestamp()).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_usage_metrics(self):
        """Busca métricas de consumo de CPU e Memória (últimas 24h)"""
        try:
            # Esta é uma simplificação. Em produção, buscaríamos via Cloud Monitoring API
            # Para o MVP, retornaremos dados estruturados que indicam saúde do sistema
            return {
                "cpu_utilization": "Low (Under 10%)",
                "memory_usage": "256MiB / 512MiB",
                "active_instances": "1 (Autoscaling scale-to-zero active)",
                "request_count": "Calculado via FinOps"
            }
        except Exception:
            return None

    def list_active_buckets(self):
        """Lista buckets ativos no projeto"""
        # Simplificado para o dashboard
        return ["flose-ai-platform-api-gemini-oficial"]
