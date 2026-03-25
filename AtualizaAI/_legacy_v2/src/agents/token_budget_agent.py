import os
from datetime import datetime

class TokenBudgetAgent:
    DAILY_BROKER_TOKEN_BUDGET = 50_000
    TOKENS_PER_AGENT_ESTIMATE = 2_000
    DAILY_TOTAL_LIMIT = 1_000_000

    def __init__(self, gcs_client):
        self.gcs = gcs_client

    def calculate_daily_agent_budget(self) -> int:
        """Calcula quantos agentes podem ser processados hoje com base no budget."""
        # Buscar gasto do dia (FinOps)
        date_str = datetime.now().strftime('%Y-%m-%d')
        daily_log = self.gcs.read_json(f"logs/finops/billing_daily_{date_str}.json") or {}
        
        used_today = daily_log.get("tokens", 0)
        broker_budget = self.DAILY_BROKER_TOKEN_BUDGET
        
        # Ajuste dinâmico se o budget total estiver apertado
        if used_today > self.DAILY_TOTAL_LIMIT * 0.7:
            broker_budget = broker_budget * 0.3
        elif used_today > self.DAILY_TOTAL_LIMIT * 0.5:
            broker_budget = broker_budget * 0.6
            
        agents_to_process = int(broker_budget / self.TOKENS_PER_AGENT_ESTIMATE)
        return max(1, agents_to_process)

    def build_priority_queue(self) -> list:
        """Retorna lista de nomes de agentes ordenados por prioridade de revisão."""
        registry = self.gcs.read_json("agents/registry.json") or {"agents": []}
        all_agents = registry.get("agents", [])
        
        core_agents = [
            "FinOpsGuardian", "CognitiveOrchestrator", "VisionAgent", 
            "AudioAgent", "BriefingAgent", "ReportAgent", 
            "ProactiveAlertAgent", "EvolutionJob"
        ]
        
        # Filtrar dinâmicos
        dynamic = [a for a in all_agents if a["agent_name"] not in core_agents]
        
        # Lógica de priorização
        # 1. Crônicos (reprovados > 1 vez)
        # 2. Primeira falha
        # 3. Nunca revisados (sem certified)
        # 4. Antigos certificados (mais de 30 dias)
        
        priority_list = []
        
        # Nunca revisados ou crônicos primeiro
        dynamic.sort(key=lambda x: (
            x.get("certified", -1), # -1 n/a, False 0, True 1
            -x.get("certification_attempts", 0),
            x.get("created_at", "")
        ))
        
        return [a["agent_name"] for a in dynamic]

    def log_budget_decision(self, agents_allowed, reason):
        date_str = datetime.now().strftime('%Y%m%d')
        file_path = f"logs/broker/budget_{date_str}.json"
        
        log_entry = {
            "date": date_str,
            "agents_allowed": agents_allowed,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.gcs.upload_json(log_entry, file_path)
