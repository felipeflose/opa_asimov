import logging
import os
import json
import time
import threading
from datetime import datetime

from agent_core import load_graph, save_graph, slugify, VAULT_PATH, get_model
from agent_parser import parse_filename
from agent_enricher import enrich_node
from agent_pregraph import generate_global_taxonomy

logger = logging.getLogger(__name__)

# Lock para garantir integridade do JSON em processamento paralelo
graph_lock = threading.Lock()

def process_node(file_path, nodes_map, active_links, should_save=True):
    filename = os.path.basename(file_path)
    
    # 1. PARSER: Extrai metadados estruturais do nome do arquivo (sem LLM)
    parsed = parse_filename(filename)
    n_type = parsed["type"]
    category_id = parsed["category_hub_id"]
    category_title = parsed["category_hub_title"]
    type_id = parsed["type_hub_id"]
    leaf_id = slugify(filename.replace(".md", ""))
    
    # Ignorar arquivos do próprio OpenClaw se não for o desejado, mas vamos inclui-los
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Erro ao ler {filename}: {e}")
        return

    # 2. ENRICH: Extrai informações semânticas (1 LLM call)
    # Tenta obter do cache se o arquivo não mudou (aqui vamos reprocessar sempre para simplificar)
    model = get_model()
    enriched = enrich_node(content, filename, n_type, parsed["section"], model=model)
    
    # 3. MATERIALIZATION (COM LOCK)
    with graph_lock:
        # Garante o Type Hub
        if type_id not in nodes_map:
            nodes_map[type_id] = {"id": type_id, "title": f"📍 {type_id.replace('_hub', '').upper()}", "type": n_type, "integrated": True, "depth": 1}
        if not any(e['source'] == 'mestre' and e['target'] == type_id for e in active_links):
            active_links.append({"source": "mestre", "target": type_id, "reasoning": "Eixo central"})
            
        # Garante o Category Hub
        if category_id not in nodes_map:
            nodes_map[category_id] = {"id": category_id, "title": category_title, "type": n_type, "integrated": True, "depth": 2}
        if not any(e['source'] == type_id and e['target'] == category_id for e in active_links):
            active_links.append({"source": type_id, "target": category_id, "reasoning": "Categoria"})
            
        # Garante o Grouping Hub (se o LLM retornou um agrupador válido)
        grouping_name = enriched.get("grouping_hub", "").strip()
        parent_for_leaf = category_id
        leaf_depth = 3
        
        if grouping_name and len(grouping_name) > 2 and grouping_name.lower() != "nenhum":
            grouping_id = f"group_{slugify(grouping_name)}"
            if grouping_id not in nodes_map:
                nodes_map[grouping_id] = {
                    "id": grouping_id, 
                    "title": grouping_name, 
                    "type": n_type, 
                    "integrated": True, 
                    "depth": 3
                }
            if not any(e['source'] == category_id and e['target'] == grouping_id for e in active_links):
                active_links.append({"source": category_id, "target": grouping_id, "reasoning": "Agrupamento Estratégico"})
            parent_for_leaf = grouping_id
            leaf_depth = 4
            
        # Cria o Leaf Node
        s_title = enriched.get("short_name", enriched.get("strategic_title", parsed["name"]))
        nodes_map[leaf_id] = {
            "id": leaf_id,
            "title": s_title,
            "strategic_title": enriched.get("strategic_title", ""),
            "type": n_type,
            "integrated": True,
            "depth": leaf_depth,
            "path": file_path,
            "summary": enriched.get("summary", ""),
            "tags": enriched.get("tags", [])
        }
        
        # Link do Parent Hub para o Leaf Node
        if not any(e['source'] == parent_for_leaf and e['target'] == leaf_id for e in active_links):
            active_links.append({"source": parent_for_leaf, "target": leaf_id, "reasoning": "Documento"})

        if should_save:
            save_graph(list(nodes_map.values()), active_links, f"✨ Indexado: {s_title}")
        logger.info(f"Processado: {filename}")

def sync_local_vault():
    logger.info(f"Sincronizando vault local a partir de: {VAULT_PATH}")
    if not os.path.exists(VAULT_PATH):
        logger.warning(f"Diretório do Vault {VAULT_PATH} não existe. Criando diretório vazio...")
        os.makedirs(VAULT_PATH, exist_ok=True)
        return

def generate_graph():
    sync_local_vault()
    
    # Inicia um novo grafo limpo em vez de carregar a sujeira anterior
    # Mas para não perder layouts salvos, vamos carregar e limpar.
    graph_data = load_graph()
    old_nodes = {n['id']: n for n in graph_data.get('nodes', [])}
    
    # Recomeçamos as edges para limpar os caminhos gigantes antigos
    active_links = []
    nodes_map = {}

    # Inicialização Core (Resiliência)
    core_nodes = [
        {"id": "mestre", "title": "Felipe Flose", "type": "mestre", "fx": 960, "fy": 500, "integrated": True, "depth": 0},
        {"id": "mba_hub", "title": "🎓 MBA EM IA", "type": "mba", "depth": 1, "integrated": True},
        {"id": "work_hub", "title": "💼 TRABALHO", "type": "work", "depth": 1, "integrated": True},
        {"id": "tool_hub", "title": "🛠️ TECNOLOGIAS", "type": "tool", "depth": 1, "integrated": True},
        {"id": "classificar_hub", "title": "🔍 CLASSIFICAR", "type": "classificar", "depth": 1, "integrated": True}
    ]
    core_edges = [
        {"source": "mestre", "target": "mba_hub", "reasoning": "Eixo central"},
        {"source": "mestre", "target": "work_hub", "reasoning": "Eixo central"},
        {"source": "mestre", "target": "tool_hub", "reasoning": "Eixo central"},
        {"source": "mestre", "target": "classificar_hub", "reasoning": "Eixo central"}
    ]
    for cn in core_nodes:
        # Recupera fx e fy se existirem
        if cn['id'] in old_nodes:
            cn['fx'] = old_nodes[cn['id']].get('fx', cn.get('fx'))
            cn['fy'] = old_nodes[cn['id']].get('fy', cn.get('fy'))
        nodes_map[cn['id']] = cn
        
    for ce in core_edges:
        active_links.append(ce)

    # Salva o estado inicial (core) imediatamente
    save_graph(list(nodes_map.values()), active_links, "💎 Inicializando estrutura core V2...")

    # FASE 1: PRE-GRAPH GLOBAL (Taxonomia)
    generate_global_taxonomy(VAULT_PATH, get_model())

    files = [os.path.join(VAULT_PATH, f) for f in os.listdir(VAULT_PATH) if f.endswith('.md')]
    logger.info(f"Iniciando processamento V2 (Fase 2) de {len(files)} arquivos...")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    max_workers = 3
    sem = threading.Semaphore(max_workers)
    
    def worker(f_path):
        with sem:
            process_node(f_path, nodes_map, active_links, should_save=False)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, f_path): f_path for f_path in files}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 5 == 0 or completed == len(files):
                save_graph(list(nodes_map.values()), active_links, f"✨ Sincronizando: {completed}/{len(files)} arquivos...")

    # Fase 4: CROSS-LINKS (Baseado em Tags, 0 LLMs)
    logger.info("Criando cross-links por tags...")
    for n1 in list(nodes_map.values()):
        if n1.get('depth', 0) == 3 and n1.get('tags'):
            for tag in n1['tags']:
                tag_norm = slugify(tag)
                # Procura por leafs ou hubs que correspondam a tag
                for n2 in list(nodes_map.values()):
                    if n1['id'] == n2['id']: continue
                    
                    match = False
                    if slugify(n2.get('title','')) == tag_norm:
                        match = True
                    elif tag_norm in n2['id']:
                        match = True
                        
                    if match:
                        edge_exists = any((e['source'] == n1['id'] and e['target'] == n2['id']) or (e['source'] == n2['id'] and e['target'] == n1['id']) for e in active_links)
                        if not edge_exists:
                            active_links.append({"source": n1['id'], "target": n2['id'], "reasoning": f"Cross-link tag: {tag}", "cross_link": True})

    save_graph(list(nodes_map.values()), active_links, "✅ Grafo V2 gerado com sucesso!")
    logger.info("Processamento V2 concluído.")

if __name__ == "__main__":
    generate_graph()
