import os

class AgentMarketplace:
    def __init__(self, gcs_client):
        self.gcs = gcs_client
        self.market_path = "marketplace/templates/"

    async def export_agent(self, agent_name: str):
        """Transforma um agente local em um template público com visual persistido no GCS."""
        agent_data = self.gcs.read_json(f"agents/{agent_name}.json")
        if not agent_data:
            return None
        
        # 1. Gerar e Persistir Visual via GCS (Soberania de Dados)
        napkin_visual_url = None
        try:
            from src.utils.napkin_client import NapkinClient
            napkin = NapkinClient()
            content_for_visual = f"Agent: {agent_data['agent_name']}. Purpose: {agent_data['purpose']}. {agent_data['system_prompt'][:400]}"
            
            # Usar o método que já faz o upload para GCS
            ts = os.urandom(4).hex()
            persistent_path = await napkin.generate_and_upload_to_gcs(
                content_for_visual, 
                self.gcs, 
                f"market_{agent_name.lower()}_{ts}.svg"
            )
            napkin_visual_url = persistent_path
        except Exception as e:
            print(f"Napkin visual persistence failed: {e}")

        # 2. Limpa métricas privadas antes de exportar
        template = {
            "name": agent_data["agent_name"],
            "purpose": agent_data["purpose"],
            "system_prompt": agent_data["system_prompt"],
            "tools": agent_data.get("tools", []),
            "avatar": agent_data.get("avatar"),
            "author": "Flose Community",
            "napkin_visual_url": napkin_visual_url  # URL final persistida no GCS
        }
        
        filename = f"{self.market_path}{agent_name.lower()}_template.json"
        self.gcs.upload_json(template, filename)
        return filename

    def list_templates(self):
        """Lista todos os templates disponíveis no Marketplace."""
        try:
            import json
            blobs = self.gcs.bucket.list_blobs(prefix=self._full_market_path())
            templates = []
            for blob in blobs:
                if blob.name.endswith('_template.json'):
                    content = blob.download_as_text()
                    data = json.loads(content)
                    if data:
                        templates.append(data)
            return templates
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []

    def _full_market_path(self):
        """Retorna o path completo incluindo o user namespace."""
        return f"users/{self.gcs.user_id}/{self.market_path}"

