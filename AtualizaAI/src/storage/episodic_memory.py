from datetime import datetime, timedelta
import json

class EpisodicMemory:
    def __init__(self, gcs_client=None):
        self.gcs_client = gcs_client
        self.episodes = []
        self.path = "memory/episodes.json"
        self.load()

    def add(self, content: str, agent: str, tags: list = None):
        ep = {
            "id": f"ep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "ts": datetime.now().isoformat(),
            "content": content,
            "agent": agent,
            "tags": tags or []
        }
        self.episodes.append(ep)
        self._save()

    def recall(self, query: str, top_k=5, days_back=30) -> list:
        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()
        recent = [e for e in self.episodes if e["ts"] > cutoff]
        query_words = set(query.lower().split())
        scored = []
        for ep in recent:
            overlap = len(query_words & set(ep["content"].lower().split()))
            days_old = (datetime.now() - datetime.fromisoformat(ep["ts"])).days
            score = (overlap * 0.7) + (max(0.1, 1 - days_old / days_back) * 0.3)
            scored.append((score, ep))
        scored.sort(reverse=True)
        return [ep for _, ep in scored[:top_k]]

    def _save(self):
        if self.gcs_client:
            self.gcs_client.upload_json({"episodes": self.episodes}, self.path)

    def load(self):
        if self.gcs_client:
            try:
                data = self.gcs_client.read_json(self.path)
                if data:
                    self.episodes = data.get("episodes", [])
            except Exception:
                self.episodes = []
