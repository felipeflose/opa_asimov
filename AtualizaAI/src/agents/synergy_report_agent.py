import google.generativeai as genai
import os
import json
from datetime import datetime, timedelta

class SynergyReportAgent:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_report(self):
        """Analisa a sinergia entre agentes na última semana."""
        if not self.gcs_client:
            return "Erro: GCS Client não configurado."

        try:
            # 1. Matriz de Afinidade
            affinity = self.gcs_client.read_json("agents/affinity_matrix.json") or {"interactions": {}}
            
            # 2. Logs de Execução da última semana
            one_week_ago = datetime.now() - timedelta(days=7)
            prefix = f"users/{self.gcs_client.user_id}/logs/executions/"
            blobs = list(self.gcs_client.bucket.list_blobs(prefix=prefix))
            
            weekly_logs = []
            for blob in blobs:
                if blob.updated.replace(tzinfo=None) > one_week_ago:
                    data = self.gcs_client.read_json(blob.name.replace(f"users/{self.gcs_client.user_id}/", ""))
                    if data:
                        weekly_logs.append(data)

            # 3. Preparação para o Gemini
            prompt = f"""
            Você é o Analista de Sinergia da Flose AI. Sua missão é gerar um relatório semanal sobre a colaboração entre nossos agentes especialistas.
            
            DADOS DA SEMANA:
            - Matriz de Afinidade (Total Histórico): {json.dumps(affinity)}
            - Execuções nos últimos 7 dias: {len(weekly_logs)}
            
            DIRETRIZES:
            1. Identifique as duplas de agentes que mais colaboraram.
            2. Identifique agentes "isolados" (com pouca ou nenhuma co-execução).
            3. Sugira uma nova "dupla dinâmica" baseada no propósito dos agentes (use sua criatividade técnica).
            4. Se houver falhas recorrentes em uma dupla, aponte.
            
            FORMATO: Markdown elegante, com emojis, direto ao ponto. Max 500 palavras.
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Erro ao gerar relatório de sinergia: {str(e)}"
