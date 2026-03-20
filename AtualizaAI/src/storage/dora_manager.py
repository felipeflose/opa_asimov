import os
import json
from datetime import datetime, timezone

class DoraManager:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.log_path = "logs/dora_metrics.json"

    def _get_data(self):
        if self.gcs_client and self.gcs_client.exists(self.log_path):
            return self.gcs_client.read_json(self.log_path)
        return {
            "deployments": [],
            "commits": [],
            "incidents": []
        }

    def _save_data(self, data):
        if self.gcs_client:
            self.gcs_client.upload_json(data, self.log_path)

    def log_commit(self, commit_hash, author, message):
        """Logs a new commit."""
        data = self._get_data()
        data.setdefault("commits", []).append({
            "hash": commit_hash,
            "author": author,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_data(data)

    def log_deployment(self, commit_hash, status="success"):
        """Logs a deployment and calculates Lead Time if the commit exists."""
        data = self._get_data()
        now = datetime.now(timezone.utc)
        
        # Calculate Lead Time
        lead_time_hours = 0.0
        commit_ts = None
        for c in data.get("commits", []):
            if c.get("hash") == commit_hash:
                try:
                    commit_ts = datetime.fromisoformat(c.get("timestamp").replace('Z', '+00:00'))
                    diff = now - commit_ts
                    lead_time_hours = diff.total_seconds() / 3600.0
                except:
                    pass
                break

        data.setdefault("deployments", []).append({
            "commit_hash": commit_hash,
            "status": status,
            "lead_time_hours": lead_time_hours,
            "timestamp": now.isoformat()
        })
        self._save_data(data)

    def get_metrics_summary(self):
        """Calculates and returns the 4 DORA metrics."""
        data = self._get_data()
        deploys = data.get("deployments", [])
        incidents = data.get("incidents", [])

        # 1. Deployment Frequency (Deploys in the last 30 days)
        now = datetime.now(timezone.utc)
        recent_deploys = []
        for d in deploys:
            try:
                ts = datetime.fromisoformat(d.get("timestamp").replace('Z', '+00:00'))
                if (now - ts).days <= 30:
                    recent_deploys.append(d)
            except:
                pass
        
        freq = len(recent_deploys)
        freq_label = f"{freq}/mês" if freq > 0 else "0/mês"

        # 2. Lead Time for Changes (Average of recent deploys)
        lead_times = [d.get("lead_time_hours", 0) for d in recent_deploys if d.get("lead_time_hours", 0) > 0]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
        lead_time_label = f"{avg_lead_time:.1f}h" if lead_times else "0.0h"

        # 3. Change Failure Rate
        failed_deploys = [d for d in recent_deploys if d.get("status") == "failed"]
        failure_rate = (len(failed_deploys) / len(recent_deploys)) * 100 if recent_deploys else 0
        failure_rate_label = f"{failure_rate:.1f}%"

        # 4. MTTR (Mean Time To Recovery)
        resolved_incidents = [i for i in incidents if i.get("status") == "resolved" and i.get("mttr_hours") is not None]
        mttr_times = [i.get("mttr_hours") for i in resolved_incidents]
        avg_mttr = sum(mttr_times) / len(mttr_times) if mttr_times else 0
        mttr_label = f"{avg_mttr:.1f}h" if mttr_times else "0.0h"

        return {
            "deployment_frequency": freq_label,
            "lead_time": lead_time_label,
            "change_failure_rate": failure_rate_label,
            "mttr": mttr_label,
            "raw": {
                "total_deploys_30d": freq,
                "avg_lead_time_hours": avg_lead_time,
                "failure_rate_pct": failure_rate,
                "avg_mttr_hours": avg_mttr,
                "open_incidents": len([i for i in incidents if i.get("status") == "open"])
            }
        }
