import json
from datetime import datetime

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

    def get_daily_summary(self):
        if self.gcs_client and self.gcs_client.exists(self.log_path):
            return self.gcs_client.read_json(self.log_path)
        return {}
