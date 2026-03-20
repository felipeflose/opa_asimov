import os
import json
from datetime import datetime, timezone

class SharedMemory:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.path = "agents/shared_memory.json"

    def _get_data(self):
        if self.gcs_client and self.gcs_client.exists(self.path):
            return self.gcs_client.read_json(self.path)
        return {"memories": []}

    def _save_data(self, data):
        if self.gcs_client:
            self.gcs_client.upload_json(data, self.path)

    def write(self, agent, key, value):
        """Grava uma nova descoberta na memória compartilhada."""
        data = self._get_data()
        memories = data.get("memories", [])
        
        # Manter apenas um histórico razoável (100 itens)
        if len(memories) >= 100:
            memories.pop(0)

        memories.append({
            "agent": agent,
            "key": key.lower(),
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        data["memories"] = memories
        self._save_data(data)

    def read_relevant(self, query=None, limit=5):
        """Lê as últimas entradas relevantes (via keyword no campo key)."""
        data = self._get_data()
        memories = data.get("memories", [])
        
        if not query:
            return memories[-limit:]
            
        relevant = []
        q = query.lower()
        # Busca reversa (mais recentes primeiro)
        for m in reversed(memories):
            if q in m.get("key", "") or q in str(m.get("value", "")).lower():
                relevant.append(m)
                if len(relevant) >= limit:
                    break
        return relevant
