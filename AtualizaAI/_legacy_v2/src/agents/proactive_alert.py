from datetime import datetime, timedelta
from collections import Counter
import httpx
import os

class ProactiveAlertAgent:
    def __init__(self, kg_manager, gcs_client, orchestrator):
        self.kg = kg_manager
        self.gcs = gcs_client
        self.orchestrator = orchestrator
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def analyze(self) -> list:
        alerts = []
        graph = self.kg.graph
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        agent_purposes = " ".join(a.get("purpose","").lower() for a in registry["agents"])

        # Regra 1: conceito frequente sem agente especialista
        concepts = [n for n in graph.nodes() if graph.nodes[n].get("type") == "concept"]
        for concept in concepts:
            degree = graph.degree(concept)
            # Se o conceito é mencionado muito mas não está no propósito de nenhum agente
            if degree >= 3 and concept.lower() not in agent_purposes:
                alerts.append(f"🧬 Padrão detectado: O conceito '{concept}' foi mencionado {degree}x, mas não identifiquei um agente especialista. Sugestão: Criar 'Agente {concept}'.")

        # Regra 2: agente sem execução há 7 dias
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        for agent in registry["agents"]:
            agent_name = agent['agent_name']
            perf = self.gcs.read_json(f"agents/performance/{agent_name}.json")
            if perf and perf.get("history"):
                last_exec = perf["history"][-1]["ts"]
                if last_exec < cutoff:
                    alerts.append(f"💤 Inatividade: O agente '{agent_name}' não executa tarefas há mais de 7 dias. Ele ainda é necessário para a operação?")

        # Regra 3: custo acima da média dos últimos 7 dias
        finops = self.gcs.read_json("logs/finops/billing_daily.json") or {}
        # Garante que as chaves estão ordenadas por data
        sorted_dates = sorted(finops.keys())
        recent_dates = sorted_dates[-7:]
        recent_costs = [finops[d].get("cost", 0) for d in recent_dates]
        
        if len(recent_costs) >= 3:
            avg_cost = sum(recent_costs[:-1]) / (len(recent_costs) - 1)
            today_cost = recent_costs[-1]
            if today_cost > avg_cost * 1.5 and today_cost > 0.1: # Evita disparar por centavos
                alerts.append(f"💸 Alerta de Custo: O consumo de hoje (${today_cost:.3f}) está 50% acima da média recente (${avg_cost:.3f}).")

        return alerts

    async def notify(self):
        alerts = self.analyze()
        if not alerts:
            print("Nenhum alerta proativo gerado.")
            return
            
        header = "🛡️ **ALERTA PROATIVO - MONITORAMENTO FLOSE AI**\n\n"
        msg = header + "\n\n".join(f"• {a}" for a in alerts)
        
        if not self.token or not self.chat_id:
            print(f"Alertas gerados mas Telegram não configurado:\n{msg}")
            return

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"https://api.telegram.org/bot{self.token}/sendMessage",
                    json={"chat_id": self.chat_id, "text": msg, "parse_mode": "Markdown"}
                )
                if resp.status_code != 200:
                    print(f"Erro ao enviar alertas: {resp.text}")
            except Exception as e:
                print(f"Erro na conexão com Telegram para alertas: {e}")
