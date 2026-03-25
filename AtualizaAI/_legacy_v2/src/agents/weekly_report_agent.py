import os
import json
import httpx
from datetime import datetime, timedelta
from src.storage.gcs_client import GCSClient

class WeeklyReportAgent:
    def __init__(self, gcs_client: GCSClient, orchestrator):
        self.gcs = gcs_client
        self.orchestrator = orchestrator
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    async def generate_and_send(self):
        # 1. Obter logs da última semana
        time_threshold = datetime.utcnow() - timedelta(days=7)
        executions = []
        
        try:
            # Usamos o prefixo direto do bucket
            prefix = f"users/{self.gcs.user_id}/logs/executions/"
            blobs = list(self.gcs.bucket.list_blobs(prefix=prefix))
            
            for blob in blobs:
                # blob.updated é em UTC
                if blob.updated.replace(tzinfo=None) > time_threshold:
                    # Remove o prefixo do usuário para ler via gcs_client.read_json
                    path = blob.name.replace(f"users/{self.gcs.user_id}/", "")
                    data = self.gcs.read_json(path)
                    if data:
                        executions.append(data)
        except Exception as e:
            print(f"Error fetching logs for weekly report: {e}")

        if not executions:
            report_text = "_Nenhuma execução registrada via agentes na última semana._"
        else:
            # 2. Sumarizar com Gemini via Orchestrator
            executions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            summary_input = json.dumps(executions[:40]) # Limite razoável para o prompt
            
            prompt = f"""
            Você é o Chefe de Operações (COO) da Flose AI. 
            Analise a lista de execuções de agentes da última semana e gere um resumo executivo premium para o Diretor.
            
            DADOS DAS EXECUÇÕES DA SEMANA:
            {summary_input}
            
            ESTRUTURA DO RELATÓRIO:
            1. 📊 **Status das Operações**: Total de execuções e volume de atividade.
            2. 🎯 **Marcos Alcançados**: Destaques das entregas baseados nos resultados das tasks.
            3. 🦾 **Aprendizado da IA**: Como o sistema evoluiu com base nessas ações.
            
            REGRAS:
            - Tom de voz: Formal, profissional e tecnológico.
            - Linguagem: Português do Brasil.
            - Use negrito e emojis para leitura rápida no Telegram.
            """
            
            decision = self.orchestrator.process_command(prompt)
            report_text = decision.get("response", "Houve um erro técnico ao consolidar o relatório da semana.")

        # 3. Enviar no Telegram
        final_msg = f"🗓️ **CONSOLIDAÇÃO SEMANAL DE OPERAÇÕES**\n\n{report_text}"
        
        if self.token and self.chat_id:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": final_msg, "parse_mode": "Markdown"}
                )
        
        return {"status": "ok", "executions_count": len(executions)}
