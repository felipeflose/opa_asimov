import json
import os
from dotenv import load_dotenv
from src.storage.gcs_client import GCSClient
import networkx as nx

load_dotenv()

def deep_clean():
    bucket_name = "flose-ai-platform-api-gemini-oficial"
    project_id = os.getenv("GCP_PROJECT_ID")
    remote_path = "knowledge/global_graph.json"
    
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    if gcs.exists(remote_path):
        print("📥 Lendo grafo para reset técnico...")
        data = gcs.read_json(remote_path)
        
        # Corrige formato de links se necessário
        if "edges" in data and "links" not in data:
            data["links"] = data.pop("edges")
            
        graph = nx.node_link_graph(data)
        
        # 1. Identifica nós para deletar (Limpeza Agressiva)
        nodes_to_remove = [
            node for node in graph.nodes() 
            if str(node).startswith("Interação") 
            or str(node).startswith("Command") 
            or str(node).startswith("TG:")
            or graph.nodes[node].get('type') == 'task'
            or str(node) in ["Orchestrator", "Generated_MVP", "Learnings", "Potential_MVP"]
        ]
        
        # 2. Executa a limpeza
        print(f"🗑️ Deletando {len(nodes_to_remove)} nós de ruído...")
        for node in nodes_to_remove:
            graph.remove_node(node)
            
        # 3. Garante que o nó Flose é o SOL Dourado
        root = "Flose"
        if root not in graph:
            graph.add_node(root, type="core")
            
        # Mapeamento Global de Pilares (Azuis)
        category_map = {
            "PowerBI": "DataViz", "Tableau": "DataViz", "Looker": "DataViz", "Metabase": "DataViz",
            "BigQuery": "GCP Infrastructure", "ElevenLabs": "AI Models", "Gemini": "AI Models",
            "dbt": "Data Engineering", "SQL": "Data Engineering", "Python": "Programming"
        }

        # Reconecta tudo nos pilares azuis
        for node in list(graph.nodes()):
            if node != root and graph.nodes[node].get('type') != "pilar":
                category = category_map.get(node, "AI Architecture")
                
                if category not in graph:
                    graph.add_node(category, type="pilar")
                    graph.add_edge(root, category)
                
                if not graph.has_edge(category, node):
                    graph.add_edge(category, node)

        # 4. Salva de volta
        new_data = nx.node_link_data(graph)
        if "links" in new_data:
            new_data["edges"] = new_data.pop("links")
            
        gcs.upload_json(new_data, remote_path)
        print("✅ Grafo limpo e reestruturado com sucesso!")
    else:
        print("❌ Grafo não encontrado.")

if __name__ == "__main__":
    deep_clean()
