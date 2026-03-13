from src.agents.base_agent import BaseAgent
import json

class FinOpsGuardian(BaseAgent):
    def __init__(self, gcs_client=None, token_limit=1000000, cost_limit=10.0):
        super().__init__(
            name="FinOpsGuardian",
            purpose="Monitor costs and token usage; block expensive executions.",
            tools=["token_estimator", "cost_analyzer"],
            gcs_client=gcs_client
        )
        self.token_limit = token_limit
        self.cost_limit = cost_limit

    def estimate_tokens(self, text):
        # Rough estimation: 1 token ~= 4 chars
        return len(text) // 4

    def check_execution(self, estimated_tokens, estimated_infra_cost=0):
        """
        Garantindo controle absoluto de custos.
        Ele bloqueia: execuções caras, deploy caro, excesso de tokens.
        """
        # Load current usage from GCS (Iceberg table simulation for now)
        current_usage = self.gcs_client.read_json("logs/daily_usage.json") if self.gcs_client else {"tokens": 0, "cost": 0}
        
        projected_tokens = current_usage.get("tokens", 0) + estimated_tokens
        projected_cost = current_usage.get("cost", 0) + estimated_infra_cost # Simple sum for demo
        
        if projected_tokens > self.token_limit:
            return False, "BLOCK EXECUTION: Token limit exceeded"
        
        if projected_cost > self.cost_limit:
            return False, "BLOCK EXECUTION: Cost limit exceeded"
        
        return True, "Execution approved"

    def run(self, task_metadata):
        # logic to validate a task before allowing it to proceed
        tokens = self.estimate_tokens(task_metadata.get("input", ""))
        infra_cost = task_metadata.get("infra_cost", 0)
        
        approved, message = self.check_execution(tokens, infra_cost)
        
        log_entry = {
            "timestamp": "now",
            "agent": "FinOpsGuardian",
            "decision": message,
            "approved": approved
        }
        if self.gcs_client:
            self.gcs_client.upload_json(log_entry, f"logs/finops_{task_metadata.get('task_id')}.json")
            
        return approved, message
