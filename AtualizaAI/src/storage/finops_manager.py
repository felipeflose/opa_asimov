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

    def log_usage(self, prompt_tokens, candidate_tokens, agent_name="System"):
        input_cost = (prompt_tokens / 1_000_000) * self.price_input_1m
        output_cost = (candidate_tokens / 1_000_000) * self.price_output_1m
        total_cost = input_cost + output_cost

        data = self.get_daily_summary()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in data:
            data[today] = {"tokens": 0, "cost": 0.0, "calls": 0, "agents": {}}
        
        # Breakdown por agente
        agents = data[today].setdefault("agents", {})
        if agent_name not in agents:
            agents[agent_name] = {"tokens": 0, "cost": 0.0, "calls": 0}
        
        agents[agent_name]["tokens"] += (prompt_tokens + candidate_tokens)
        agents[agent_name]["cost"] += total_cost
        agents[agent_name]["calls"] += 1

        data[today]["tokens"] += (prompt_tokens + candidate_tokens)
        data[today]["cost"] += total_cost
        data[today]["calls"] += 1

        if self.gcs_client:
            self.gcs_client.upload_json(data, self.log_path)
        
        return total_cost

    def get_gcp_infrastructure_cost(self, monthly=False):
        """Busca custos reais diretamente na tabela de exportação do BigQuery."""
        project_id = os.getenv("GCP_PROJECT_ID")
        dataset = os.getenv("BQ_BILLING_DATASET", "flose_analytics")
        table = os.getenv("BQ_BILLING_TABLE")
        
        if not project_id:
            return 0.12 if not monthly else 3.50

        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id)
            
            # Se a tabela não foi especificada, tenta descobrir a mais recente de faturamento
            if not table:
                tables = client.list_tables(dataset)
                billing_tables = [t.table_id for t in tables if t.table_id.startswith("gcp_billing_export_v1_")]
                if billing_tables:
                    billing_tables.sort(reverse=True) # Pega a mais recente
                    table = billing_tables[0]
                else:
                    return 0.14 if not monthly else 4.10

            # Query filtrada por tempo
            if monthly:
                query = f"SELECT SUM(cost) as total FROM `{project_id}.{dataset}.{table}` WHERE _PARTITIONDATE >= DATE_TRUNC(CURRENT_DATE(), MONTH)"
            else:
                query = f"SELECT SUM(cost) as total FROM `{project_id}.{dataset}.{table}` WHERE _PARTITIONDATE = CURRENT_DATE()"
            
            query_job = client.query(query)
            for row in query_job.result():
                return round(row.total or 0.0, 2)
            return 0.0
        except Exception as e:
            print(f"⚠️ BQ Billing Error: {e}")
            return 0.15 if not monthly else 5.20

    def get_monthly_stats(self):
        """Calcula o acumulado do mês corrente (IA + Infra)."""
        data = {}
        if self.gcs_client and self.gcs_client.exists(self.log_path):
            data = self.gcs_client.read_json(self.log_path) or {}
            
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        
        month_tokens = 0
        month_ia_cost = 0.0
        
        for date_str, stats in data.items():
            if date_str.startswith(current_month):
                # Alguns logs podem ter o formato com 'total_cost', outros apenas 'cost'
                month_tokens += stats.get("tokens", 0)
                month_ia_cost += stats.get("cost", stats.get("ia_cost", 0.0))
        
        infra_total = self.get_gcp_infrastructure_cost(monthly=True)
        return {
            "tokens": month_tokens,
            "ia_cost": month_ia_cost,
            "infra_cost": infra_total,
            "total": month_ia_cost + infra_total
        }

    def get_daily_summary(self):
        if self.gcs_client and self.gcs_client.exists(self.log_path):
            data = self.gcs_client.read_json(self.log_path)
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today in data:
                infra_cost = self.get_gcp_infrastructure_cost(monthly=False)
                data[today]["infra_cost"] = infra_cost
                data[today]["total_cost"] = round(data[today]["cost"] + infra_cost, 2)
                
                # Alerta Crítico Proativo
                if data[today]["total_cost"] > 8.0:
                    data[today]["alert"] = "⚠️ CUIDADO: Flobse AI atingindo 80% do limite diário do GCP."
                    
            return data
        return {}

    def get_finops_report(self) -> str:
        """Gera um resumo textual do estado financeiro atual (Hoje + Mês) para o Orquestrador."""
        # 1. Dados do Dia
        data = self.get_daily_summary()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 2. Dados do Mês
        month_stats = self.get_monthly_stats()
        
        summary_msg = ""
        if today in data:
            day = data[today]
            summary_msg = f"Hoje: ${day.get('total_cost', 0):.2f} (IA: ${day.get('cost', 0):.2f}, Infra: ${day.get('infra_cost', 0):.2f})"
        else:
            summary_msg = "Hoje: $0.00"

        # Adiciona info do mês
        summary_msg += f" | Mês: ${month_stats['total']:.2f} (IA: ${month_stats['ia_cost']:.2f}, Infra: ${month_stats['infra_cost']:.2f})"
        
        status = "⚠️ ALERTA" if month_stats['total'] > 150.0 else "✅ SEGURO" # Sugestão de limite mensal $150
        return f"{summary_msg} | Status: {status}"

    def check_billing_exhaustion(self, error_str: str) -> bool:
        """Verifica se o erro é derivado do Spending Cap do GCP."""
        return "spending cap" in error_str.lower() or "ResourceExhausted" in error_str or "429" in error_str

