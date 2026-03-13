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

    def _sanitize(self):
        """Remove nós de ruído e garante a estrutura core."""
        nodes_to_remove = [
            node for node in self.graph.nodes() 
            if str(node).startswith("Interação") 
            or str(node).startswith("Command") 
            or str(node).startswith("TG:")
            or self.graph.nodes[node].get('type') == 'task'
        ]
        for node in nodes_to_remove:
            self.graph.remove_node(node)
        
        if "Flose" not in self.graph:
            self.graph.add_node("Flose", type="core")

    def add_interaction(self, agent_name, task_name, outcome):
        """
        Sincroniza e adiciona apenas conceitos técnicos, conectando-os
        diretamente aos pilares de conhecimento com limpeza proativa.
        """
        self.load()
        self._sanitize() # Limpeza proativa
        
        learned_concepts = outcome.get("learned_concepts", [])
        if not learned_concepts:
            self.save() # Salva a limpeza mesmo sem novos conceitos
            return

        # Mapeamento Inteligente de Categorias
        category_map = {
            "PowerBI": "DataViz", "Tableau": "DataViz", "Looker": "DataViz", "Metabase": "DataViz", 
            "Plotly": "DataViz", "Streamlit": "DataViz", "BigQuery": "GCP Infrastructure", 
            "Firestore": "GCP Infrastructure", "Cloud Run": "GCP Infrastructure", "GCS": "GCP Infrastructure",
            "Gemini": "AI Models", "ElevenLabs": "AI Models", "Terraform": "DevOps", "Docker": "DevOps",
            "Python": "Programming", "SQL": "Data Engineering", "FinOps": "FinOps"
        }

        for concept in learned_concepts:
            concept = concept.strip()
            if concept and len(concept) < 40 and not any(noise in concept for noise in ["Interação", "Command", "TG:"]):
                self.graph.add_node(concept, type="concept", color="green")
                
                category = "AI Architecture"
                for key, val in category_map.items():
                    if key.lower() in concept.lower():
                        category = val
                        break
                
                if category not in self.graph:
                    self.graph.add_node(category, type="pilar", color="#f59e0b")
                    self.graph.add_edge("Flose", category)

                self.graph.add_edge(category, concept, relation="groups")

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
