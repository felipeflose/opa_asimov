import google.generativeai as genai
import json
import os
from datetime import datetime

class BaseAgent:
    def __init__(self, name, purpose, system_prompt=None, avatar=None, tools=None, gcs_client=None):
        self.name = name
        self.purpose = purpose
        self.system_prompt = system_prompt or f"Você é o {self.name}, um agente especializado em {self.purpose}."
        self.avatar = avatar or "https://api.dicebear.com/7.x/bottts/svg?seed=" + self.name
        self.tools = tools or []
        self.gcs_client = gcs_client
        self.memory_path = f"agents/memory/{self.name}/"
        
    def to_dict(self):
        return {
            "agent_name": self.name,
            "purpose": self.purpose,
            "system_prompt": self.system_prompt,
            "avatar": self.avatar,
            "tools": self.tools,
            "memory": self.memory_path,
            "token_cost_profile": "standard",
            "created_at": datetime.now().isoformat()
        }

    def save_to_registry(self):
        if self.gcs_client:
            self.gcs_client.upload_json(self.to_dict(), f"agents/{self.name}.json")
            # Also update registry.json
            registry = self.gcs_client.read_json("agents/registry.json") or {"agents": []}
            
            # Update or Append
            found = False
            for i, a in enumerate(registry['agents']):
                if a['agent_name'] == self.name:
                    registry['agents'][i] = self.to_dict()
                    found = True
                    break
            
            if not found:
                registry['agents'].append(self.to_dict())
                
            self.gcs_client.upload_json(registry, "agents/registry.json")

    def run(self, task):
        raise NotImplementedError("Each agent must implement its own run method.")
