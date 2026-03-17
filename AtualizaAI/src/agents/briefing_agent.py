from datetime import datetime, timedelta
import os
import httpx
import google.generativeai as genai

class BriefingAgent:
    def __init__(self, orchestrator, gcs_client):
        self.orchestrator = orchestrator
        self.gcs = gcs_client
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def generate(self) -> str:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Coleta dados de FinOps
        finops = self.gcs.read_json("logs/finops/billing_daily.json") or {}
        # Tenta pegar faturamento real ou mockado
        stats = finops.get(yesterday, {"tokens": 0, "cost": 0.0, "calls": 0})
        
        # Coleta demandas
        demands = self.gcs.read_json("demands/registry.json") or {"demands": []}
        open_d = [d["title"] for d in demands["demands"] if d["status"] == "Aberto"]
        
        # Coleta novos agentes
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        new_agents = [a["agent_name"] for a in registry["agents"] if a.get("created_at","")[:10] == yesterday]

        prompt = f"""
        Você é o Especialista em Briefing da Flose AI Platform. 
        Gere um resumo diário motivador e técnico para o seu criador.
        
        DADOS DE ONTEM ({yesterday}):
        - IA Usage: {stats.get('tokens', 0):,} tokens | Custo: ${stats.get('cost', 0.0):.4f} | Chamadas: {stats.get('calls', 0)}
        - Novos Agentes Recrutados: {', '.join(new_agents) if new_agents else 'nenhum'}
        - Pendências Urgentes: {len(open_d)} tarefas aguardando (Ex: {', '.join(open_d[:3]) if open_d else 'nenhuma'})
        
        REGRAS:
        1. Seja direto (máximo 5 linhas).
        2. Use um tom de "Secretária Executiva de Alta Performance".
        3. ⚠️ PROIBIÇÃO: Jamais invente nomes de pessoas (ex: Sophia, João). Use apenas os nomes técnicos dos agentes registrados.
        4. Termine com uma sugestão estratégica de "Próximo Passo".
        """
        
        # Usamos o orquestrador para processar o prompt de geração (ou chamamos direto o modelo)
        decision = self.orchestrator.process_command(prompt)
        return decision.get("response", "❌ Falha ao gerar briefing diário.")

    async def send(self):
        if not self.token or not self.chat_id:
            print("⚠️ Erro: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados.")
            return
            
        text = f"🌅 **BOM DIA! FLOSE AI DISPONÍVEL.**\n\n{self.generate()}"
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}
                )
                if resp.status_code != 200:
                    print(f"Erro ao enviar briefing: {resp.text}")
            except Exception as e:
                print(f"Erro na conexão com Telegram: {e}")
