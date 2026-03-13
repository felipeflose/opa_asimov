import sys
import os
import asyncio

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.agents.telegram_agent import TelegramAgent
from src.storage.gcs_client import GCSClient
from src.graph.knowledge_graph import KnowledgeGraphManager
from src.agents.vision_agent import VisionAgent
from dotenv import load_dotenv

load_dotenv()

def main():
    while True:
        try:
            # Initialize Orchestrator and GCS
            project_id = os.getenv("GCP_PROJECT_ID")
            bucket_name = f"flose-ai-platform-{project_id}"
            # v3 Fix: Explicit project pass
            gcs = GCSClient(bucket_name, project_id=project_id)
            
            orchestrator = CognitiveOrchestrator(gcs_client=gcs)
            kg = KnowledgeGraphManager(gcs_client=gcs)
            vision = VisionAgent(gcs_client=gcs)
            
            # Initialize and run Telegram Agent with GCS, KG and Vision support
            tg_agent = TelegramAgent(orchestrator, gcs_client=gcs, kg_manager=kg, vision_agent=vision)
            tg_agent.run()
        except Exception as e:
            print(f"Erro crítico no script do Bot: {e}. Reiniciando em 10 segundos...")
            import time
            time.sleep(10)

if __name__ == "__main__":
    main()
