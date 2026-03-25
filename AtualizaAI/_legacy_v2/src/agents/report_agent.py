from datetime import datetime
import os
import httpx

class ReportAgent:
    def __init__(self, gcs_client, orchestrator):
        self.gcs = gcs_client
        self.orchestrator = orchestrator
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def generate_weekly_report(self) -> str:
        # 1. Coleta resumo da semana
        finops = self.gcs.read_json("logs/finops/billing_daily.json") or {}
        total_cost = sum(v.get("cost", 0) for v in finops.values())
        
        demands = self.gcs.read_json("demands/registry.json") or {"demands": []}
        completed = [d for d in demands["demands"] if d["status"] == "Concluído"]
        
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        
        prompt = f"""
        Você é o Especialista em Reports Executivos da Flose AI Platform.
        Gere um RELATÓRIO SEMANAL DE PERFORMANCE para o cliente.
        
        INDICADORES DESTA SEMANA:
        - Investimento total em IA: ${total_cost:.2f}
        - Entregas finalizadas: {len(completed)} TRDs concluídas.
        - Tamanho da força de trabalho: {len(registry['agents'])} agentes ativos.
        
        ESTRUTURA DO REPORT:
        1. Resumo Executivo (impacto e ROI).
        2. Top 3 Projetos Concluídos.
        3. Visão de Futuro (o que a IA aprendeu esta semana).
        
        REGRAS:
        1. Use Markdown elegante. Seja formal e premium.
        2. ⚠️ PROIBIÇÃO ABSOLUTA: Não use nomes humanos genéricos (Sophia, João, Bia). Refira-se aos agentes pelos seus nomes técnicos (ex: FinOpsGuardian, TaskManager).
        3. Se não houver dados suficientes para um projeto, não invente; apenas reporte o que existe no registry.
        """
        
        decision = self.orchestrator.process_command(prompt)
        report_content = decision.get("response", "Erro ao gerar relatório.")
        
        # Salva no GCS como "delivery"
        report_id = f"REPORT_{datetime.now().strftime('%Y_%W')}"
        self.gcs.upload_json({
            "report_id": report_id,
            "content": report_content,
            "ts": datetime.now().isoformat()
        }, f"reports/{report_id}.json")
        
        return report_content

    async def send_to_telegram(self):
        report = self.generate_weekly_report()
        
        msg = f"📊 **RELATÓRIO SEMANAL DISPONÍVEL**\n\n{report[:1000]}...\n\n_Veja o report completo no GCS ou Dashboard._"
        
        if self.token and self.chat_id:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"}
                )
