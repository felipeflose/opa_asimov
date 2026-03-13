import json
import os
from dotenv import load_dotenv
from src.storage.gcs_client import GCSClient
import networkx as nx

load_dotenv()

def cleanup_graph():
    bucket_name = "flose-ai-platform-api-gemini-oficial"
    project_id = os.getenv("GCP_PROJECT_ID")
    remote_path = "knowledge/global_graph.json"
    
    gcs = GCSClient(bucket_name, project_id=project_id)
    
    if gcs.exists(remote_path):
        print("Loading graph for cleanup...")
        data = gcs.read_json(remote_path)
        
        # Ajuste para compatibilidade de versões do NetworkX
        if "edges" in data and "links" not in data:
            data["links"] = data.pop("edges")
            
        graph = nx.node_link_graph(data)
        
        nodes_to_remove = [
            node for node in graph.nodes() 
            if str(node).startswith("Command:") or str(node).startswith("TG:")
        ]
        
        if nodes_to_remove:
            print(f"Removing {len(nodes_to_remove)} unwanted nodes...")
            for node in nodes_to_remove:
                # Antes de remover, vamos tentar reconectar os filhos à Interação se possível
                # No caso do ElevenLabs, ele estava ligado ao Command. 
                # Mas já temos um nó Interação_... ligado ao Orchestrator.
                graph.remove_node(node)
            
            # Reconstrói os dados no formato que o app espera (preservando o que carregamos)
            new_data = nx.node_link_data(graph)
            
            # Se o original tinha 'edges', vamos manter 'edges' para evitar quebrar o app
            if "links" in new_data:
                new_data["edges"] = new_data.pop("links")
                
            gcs.upload_json(new_data, remote_path)
            print("Graph cleaned and saved to GCS.")
        else:
            print("No unwanted nodes found.")
    else:
        print("Graph not found in GCS.")

if __name__ == "__main__":
    cleanup_graph()
