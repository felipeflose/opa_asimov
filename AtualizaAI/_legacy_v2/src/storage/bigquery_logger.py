from google.cloud import bigquery
import os
import json
from datetime import datetime

class BigQueryLogger:
    def __init__(self, project_id=None, dataset_id="flose_analytics"):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=self.project_id)
        self.table_id = f"{self.project_id}.{self.dataset_id}.interactions"

    def log_interaction(self, agent: str, task: str, result: str, cost: float, metadata: dict = None):
        """Insere uma linha na tabela interactions do BigQuery."""
        rows_to_insert = [
            {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "task": task[:1000],
                "result": result[:5000],
                "cost_usd": float(cost),
                "metadata": json.dumps(metadata or {})
            }
        ]
        
        try:
            errors = self.client.insert_rows_json(self.table_id, rows_to_insert)
            if errors:
                print(f"Erro ao inserir no BigQuery: {errors}")
        except Exception as e:
            print(f"Falha na conexão com BigQuery: {e}")

    def query_stats(self, days=7):
        """Exemplo de query analítica para o dashboard."""
        query = f"""
            SELECT agent, COUNT(*) as total_calls, SUM(cost_usd) as total_cost
            FROM `{self.table_id}`
            WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            GROUP BY agent
            ORDER BY total_cost DESC
        """
        try:
            return self.client.query(query).to_dataframe().to_dict(orient="records")
        except Exception:
            return []
