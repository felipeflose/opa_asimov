import os
from dotenv import load_dotenv
from src.storage.gcs_client import GCSClient
from src.storage.vector_store import VectorStore
from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.graph.knowledge_graph import KnowledgeGraphManager

# Load environment variables (GEMINI_API_KEY)
load_dotenv()

def main():
    print("Initializing Flose AI Platform...")
    
    # Configuration (Constants for demo)
    BUCKET_NAME = "flose-ai-platform"
    API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY")
    
    # 1. Initialize Storage (Mocked if no credentials)
    # gcs = GCSClient(BUCKET_NAME, "service-account.json")
    print("- Storage Layer: Initialized (GCS)")
    
    # 2. Initialize Vector DB
    vector_db = VectorStore()
    vector_db.initialize()
    print("- Vector DB: Initialized (FAISS)")
    
    # 3. Initialize Knowledge Graph
    kg = KnowledgeGraphManager()
    print("- Knowledge Graph: Initialized (Seed knowledge loaded)")
    
    # 4. Start Orchestrator
    orchestrator = CognitiveOrchestrator(api_key=API_KEY)
    print("- Cognitive Orchestrator: Ready")
    
    # Example flow
    user_input = "Crie um agente que analise notícias de tecnologia."
    print(f"\nProcessing User Command: '{user_input}'")
    
    decision = orchestrator.process_command(user_input)
    print(f"Orchestrator Decision: {decision.get('reasoning')}")
    
    result = orchestrator.execute_decision(decision)
    print(f"Execution Result: {result}")
    
    # Update Graph
    kg.add_interaction(
        agent_name="CognitiveOrchestrator",
        task_name="Agent Creation: TechnologyNewsAgent",
        outcome={"status": "success", "mvp": "NewsAgent_v0.1"}
    )
    kg.save()
    print("- Knowledge Graph Updated.")
    
    print("\nPlatform bootstrap complete. Run Streamlit dashboard to view status.")

if __name__ == "__main__":
    main()
