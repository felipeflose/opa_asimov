import networkx as nx
import json
import os
from datetime import datetime

class KnowledgeGraphManager:
    def __init__(self, gcs_client=None):
        self.graph = nx.DiGraph()
        self.gcs_client = gcs_client
        self.remote_path = "knowledge/global_graph.json"
        
        # Tenta carregar o existente; se não houver, cria a base
        if not self.load():
            self._initialize_base_graph()
            self.save() # Salva a base inicial se for novo

    def _initialize_base_graph(self):
        """
        Inicialização do Knowledge Graph com conhecimento inicial:
        AI Architecture, GCP Infrastructure, FinOps, Agent Systems, Terraform, Vector Databases
        """
        self.graph.add_node("Flose", type="core")
        
        initial_topics = [
            "AI Architecture", "GCP Infrastructure", "FinOps", 
            "Agent Systems", "Terraform", "Vector Databases", "MVPs", "Code",
            "DataViz", "Databases", "AI Models", "Integration"
        ]
        
        for topic in initial_topics:
            self.graph.add_node(topic, type="pilar", color="#f59e0b")
            self.graph.add_edge("Flose", topic, relation="defined_by")

    def add_interaction(self, agent_name, task_name, outcome):
        """
        Sincroniza e adiciona apenas conceitos técnicos, conectando-os
        diretamente aos pilares de conhecimento (sem nós de 'interação').
        """
        self.load()
        
        learned_concepts = outcome.get("learned_concepts", [])
        if not learned_concepts:
            return

        # Pilares para conexão automática (fallback para 'Code' ou 'AI Architecture')
        concept_pillars = ["AI Architecture", "GCP Infrastructure", "Agent Systems", "Vector Databases", "Code"]

        # Mapeamento Inteligente e Abrangente de Categorias
        category_map = {
            # BI & DataViz
            "PowerBI": "DataViz", "Tableau": "DataViz", "Looker": "DataViz", "Metabase": "DataViz", 
            "Plotly": "DataViz", "Streamlit": "DataViz", "Grafana": "DataViz",
            
            # Cloud Infrastructure (GCP Focus)
            "BigQuery": "GCP Infrastructure", "Firestore": "GCP Infrastructure", "Cloud Run": "GCP Infrastructure",
            "GCS": "GCP Infrastructure", "Cloud Build": "GCP Infrastructure", "Vertex AI": "GCP Infrastructure",
            "Artifact Registry": "GCP Infrastructure", "App Engine": "GCP Infrastructure",
            
            # AI & ML Models
            "Gemini": "AI Models", "GPT-4": "AI Models", "Claude": "AI Models", "ElevenLabs": "AI Models",
            "Whisper": "AI Models", "Stable Diffusion": "AI Models", "LangChain": "AI Models",
            
            # Data Engineering & Databases
            "PostgreSQL": "Databases", "MongoDB": "Databases", "SQLite": "Databases", "Redis": "Databases",
            "dbt": "Data Engineering", "Airflow": "Data Engineering", "Kafka": "Data Engineering",
            "SQL": "Data Engineering", "ETL": "Data Engineering", "ELT": "Data Engineering",
            
            # DevOps & IaC
            "Terraform": "DevOps", "Docker": "DevOps", "Kubernetes": "DevOps", "GitHub Actions": "DevOps",
            "CI/CD": "DevOps", "Jenkins": "DevOps",
            
            # Software Development
            "Python": "Programming", "JavaScript": "Programming", "Go": "Programming", "FastAPI": "Programming",
            "Flask": "Programming", "Django": "Programming", "React": "Programming", "Next.js": "Programming",
            
            # Automations & Integration
            "n8n": "Automation", "Make": "Automation", "Zapier": "Automation", "REST API": "Automation",
            
            # Security & Management
            "IAM": "Security", "Secret Manager": "Security", "OAuth": "Security", "FinOps": "FinOps"
        }

        for concept in learned_concepts:
            concept = concept.strip()
            if concept and len(concept) < 40:
                self.graph.add_node(concept, type="concept", color="green")
                
                # Busca a categoria ou usa um pilar padrão inteligente
                category = "General Knowledge"
                for key, val in category_map.items():
                    if key.lower() in concept.lower():
                        category = val
                        break
                
                # Garante que o nó da categoria existe
                if category not in self.graph:
                    self.graph.add_node(category, type="pilar", color="#f59e0b")
                    self.graph.add_edge("Flose", category)

                self.graph.add_edge(category, concept, relation="groups")
                self.graph.add_edge(concept, "Code", relation="potential_integration")

        self.save()

    def save(self):
        data = nx.node_link_data(self.graph)
        if self.gcs_client:
            self.gcs_client.upload_json(data, self.remote_path)
            print("Graph saved to GCS.")
        else:
            with open("global_graph.json", "w") as f:
                json.dump(data, f)

    def load(self):
        try:
            if self.gcs_client and self.gcs_client.exists(self.remote_path):
                data = self.gcs_client.read_json(self.remote_path)
                if data:
                    self.graph = nx.node_link_graph(data)
                    print("Graph loaded from GCS.")
                    return True
            elif os.path.exists("global_graph.json"):
                with open("global_graph.json", "r") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
                    print("Graph loaded from local file.")
                    return True
        except Exception as e:
            print(f"Error loading graph: {e}")
        return False
