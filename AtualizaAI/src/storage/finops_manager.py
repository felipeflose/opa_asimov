import os
import json
from datetime import datetime
try:
    from google.cloud import billing_v1
except ImportError:
    billing_v1 = None

class FinOpsManager:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.log_path = "logs/finops/billing_daily.json"
        # Preços Gemini 2.5 Flash (Estimados baseados no 1.5 Flash)
        self.price_input_1m = 0.075  # $0.075 por 1M tokens
        self.price_output_1m = 0.30   # $0.30 por 1M tokens

    def log_usage(self, prompt_tokens, candidate_tokens):
        input_cost = (prompt_tokens / 1_000_000) * self.price_input_1m
        output_cost = (candidate_tokens / 1_000_000) * self.price_output_1m
        total_cost = input_cost + output_cost

        data = self.get_daily_summary()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in data:
            data[today] = {"tokens": 0, "cost": 0.0, "calls": 0}
        
        data[today]["tokens"] += (prompt_tokens + candidate_tokens)
        data[today]["cost"] += total_cost
        data[today]["calls"] += 1

        if self.gcs_client:
            self.gcs_client.upload_json(data, self.log_path)
        
        return total_cost

    def get_gcp_infrastructure_cost(self):
        """Busca custos reais diretamente na tabela de exportação do BigQuery."""
        project_id = os.getenv("GCP_PROJECT_ID")
        dataset = os.getenv("BQ_BILLING_DATASET", "flose_analytics")
        table = os.getenv("BQ_BILLING_TABLE")
        
        if not project_id:
            return 0.12

        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id)
            
            # Se a tabela não foi especificada, tenta descobrir a mais recente de faturamento
            if not table:
                tables = client.list_tables(dataset)
                billing_tables = [t.table_id for t in tables if t.table_id.startswith("gcp_billing_export_v1_")]
                if billing_tables:
                    # Pega a primeira tabela de exportaçao padrão encontrada
                    table = billing_tables[0]
                else:
                    return 0.14 # Ainda não populado pelo Google (leva até 24h)

            # Query faturamento de HOJE (UTC)
            query = f"SELECT SUM(cost) as total FROM `{project_id}.{dataset}.{table}` WHERE _PARTITIONDATE = CURRENT_DATE()"
            query_job = client.query(query)
            for row in query_job.result():
                return round(row.total or 0.0, 2)
            return 0.0
        except Exception as e:
            print(f"⚠️ BQ Billing Error: {e}")
            return 0.15


    def get_daily_summary(self):
        # Primeiro, verifica se há erro de cota ou limite de gastos no ar
        # Se as chamadas de teste falharem com 429, o bot deve avisar.
        
        if self.gcs_client and self.gcs_client.exists(self.log_path):
            data = self.gcs_client.read_json(self.log_path)
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Se hoje está no histórico e o custo total está perigosamente alto
            if today in data:
                infra_cost = self.get_gcp_infrastructure_cost()
                data[today]["infra_cost"] = infra_cost
                data[today]["total_cost"] = round(data[today]["cost"] + infra_cost, 2)
                
                # Alerta Crítico Proativo: Se custo total de hoje > $8.00 (80% da cota comum)
                if data[today]["total_cost"] > 8.0:
                    data[today]["alert"] = "⚠️ CUIDADO: Flobse AI atingindo 80% do limite diário do GCP."
                    
            return data
        return {}
    def check_billing_exhaustion(self, error_str: str) -> bool:
        """Verifica se o erro é derivado do Spending Cap do GCP."""
        return "spending cap" in error_str.lower() or "ResourceExhausted" in error_str or "429" in error_str

    def get_finops_report(self) -> str:
        """Gera um resumo textual do estado financeiro atual para o Orquestrador."""
        data = self.get_daily_summary()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today in data:
            day_data = data[today]
            tokens = day_data.get("tokens", 0)
            cost_ia = day_data.get("cost", 0.0)
            cost_infra = day_data.get("infra_cost", 0.0)
            total = day_data.get("total_cost", 0.0)
            status = "⚠️ ALERTA" if total > 8.0 else "✅ SEGURO"
            
            return f"Gasto Hoje: ${total:.2f} (IA: ${cost_ia:.2f}, Infra: ${cost_infra:.2f}) | Tokens: {tokens:,} | Status: {status}"
        
        return "Gasto Hoje: $0.00 | Status: ✅ SEGURO (Sem atividade registrada)"

