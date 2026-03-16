import json
import os

class AgentMarketplace:
    def __init__(self, gcs_client):
        self.gcs = gcs_client
        self.market_path = "marketplace/templates/"

    async def export_agent(self, agent_name: str):
        """Transforma um agente local em um template público com visual do Napkin AI."""
        agent_data = self.gcs.read_json(f"agents/{agent_name}.json")
        if not agent_data:
            return None
        
        # 1. Gerar Visual via Napkin AI
        from src.utils.napkin_client import NapkinClient
        napkin = NapkinClient(api_key=os.getenv("NAPKIN_API_KEY"))
        
        content_for_visual = f"Agent: {agent_data['agent_name']}\nPurpose: {agent_data['purpose']}\nFeatures: {agent_data['system_prompt'][:500]}"
        visual_res = await napkin.generate_visual(content_for_visual)
        visual_id = visual_res.get("id") if visual_res else None

        # Limpa métricas privadas antes de exportar
        template = {
            "name": agent_data["agent_name"],
            "purpose": agent_data["purpose"],
            "system_prompt": agent_data["system_prompt"],
            "tools": agent_data["tools"],
            "avatar": agent_data.get("avatar"),
            "author": "Flose Community",
            "napkin_visual_id": visual_id
        }
        
        filename = f"{self.market_path}{agent_name.lower()}_template.json"
        self.gcs.upload_json(template, filename)
        return filename

    def list_templates(self):
        """Lista templates disponíveis no marketplace."""
        files = self.gcs.list_files(self.market_path)
        templates = []
        for f in files:
            # Note: list_files returns full path
            # We need to extract the part after users/id/ to call read_json correctly if using multi-tenancy
            # But the marketplace might be global? 
            # The prompt says: "marketplace/templates/". 
            # If GCSClient prefixes everything with users/fflose/, then marketplace will be per-user unless handled.
            # I'll assume for now it's per-user as per the GCSClient change.
            path_in_user = f.replace(f"users/{self.gcs.user_id}/", "")
            data = self.gcs.read_json(path_in_user)
            if data:
                templates.append(data)
        return templates

    def import_template(self, template_name: str):
        """Cria um novo agente a partir de um template."""
        # TODO: Implementar busca por nome de arquivo se necessário
        pass
