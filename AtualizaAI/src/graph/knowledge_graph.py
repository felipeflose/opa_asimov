import networkx as nx
import json
import os
import google.generativeai as genai
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

    def deep_clean(self):
        """Lógica canônica de limpeza profunda e reestruturação do grafo."""
        self.load()
        # 1. Identifica nós para deletar
        nodes_to_remove = [
            node for node in self.graph.nodes() 
            if str(node).startswith("Interação") 
            or str(node).startswith("Command") 
            or str(node).startswith("TG:")
            or self.graph.nodes[node].get('type') == 'task'
            or str(node) in ["Orchestrator", "Generated_MVP", "Learnings", "Potential_MVP"]
        ]
        
        for node in nodes_to_remove:
            self.graph.remove_node(node)
            
        # 2. Garante raiz
        if "Flose" not in self.graph:
            self.graph.add_node("Flose", type="core")
            
        # 3. Re-clusteriza tudo via IA ou mapa estático se falhar
        for node in list(self.graph.nodes()):
            if node != "Flose" and self.graph.nodes[node].get('type') != "pilar":
                category = self._get_ai_cluster(node)
                
                if category not in self.graph:
                    self.graph.add_node(category, type="pilar")
                    self.graph.add_edge("Flose", category)
                
                if not self.graph.has_edge(category, node):
                    self.graph.add_edge(category, node)
        
        self.save()
        print("✅ Deep Clean executado com sucesso.")

    def _get_ai_cluster(self, concept):
        """Usa a inteligência do Gemini para decidir o melhor pilar de clusterização para um conceito."""
        # Se estivermos sem API Key (fallback), usamos um mapeamento básico
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "General Technology"
            
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            Classifique o conceito técnico '{concept}' em exatamente UM dos seguintes pilares de clusters:
            - AI Models (LLMs, Diffusion, etc)
            - GCP Infrastructure (Services like Cloud Run, GCS)
            - Data Engineering (ETL, SQL, dbt)
            - Programming (Python, JS, Frameworks)
            - DevOps & IaC (Terraform, Docker)
            - UI & Analytics (Streamlit, PowerBI)
            - Automation (n8n, Make)
            - FinOps & Management
            
            Responda apenas com o nome do pilar. Se não encaixar, use 'General Technology'.
            """
            response = model.generate_content(prompt)
            return response.text.strip()
        except:
            return "AI Architecture"

    def add_interaction(self, agent_name, task_name, outcome):
        """
        Sincroniza e adiciona conceitos técnicos usando Clusterização via IA.
        """
        self.load()
        self._sanitize() 
        
        learned_concepts = outcome.get("learned_concepts", [])
        if not learned_concepts:
            self.save()
            return

        for concept in learned_concepts:
            concept = concept.strip()
            # Filtro básico de ruído e tamanho
            if concept and len(concept) < 40 and not any(noise in concept.lower() for noise in ["interação", "command", "tg:"]):
                
                # NOVO: Clusterização via IA ao invés de Dict estático
                category = self._get_ai_cluster(concept)
                
                if category not in self.graph:
                    self.graph.add_node(category, type="pilar", color="#f59e0b")
                    self.graph.add_edge("Flose", category)

                self.graph.add_node(concept, type="concept", color="green")
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
