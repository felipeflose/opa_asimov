import json
import logging
import os
import re
import shutil
from datetime import datetime
from agent_core import load_graph, save_graph, slugify
import agent_core

logger = logging.getLogger(__name__)

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")


def rotate_logs():
    """Rotaciona arquivos de log da aplicação maiores que o limite configurado."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    max_log_size_mb = float(os.getenv("FLOSE_MAX_LOG_SIZE_MB", 2.0))
    max_log_size = max_log_size_mb * 1024 * 1024
    
    # Lista de locais possíveis de logs
    log_files = []
    
    # Verifica pasta logs/
    if os.path.isdir(log_dir):
        for f in os.listdir(log_dir):
            if f.endswith('.log'):
                log_files.append(os.path.join(log_dir, f))
                
    # Verifica logs soltos na raiz do projeto
    root_dir = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(root_dir):
        if f.endswith('.log') and f.startswith('server'):
            log_files.append(os.path.join(root_dir, f))
            
    for log_path in log_files:
        if os.path.isfile(log_path):
            try:
                size = os.path.getsize(log_path)
                if size > max_log_size:
                    logger.info(f"Rotacionando log {log_path} ({size / (1024*1024):.2f} MB > {max_log_size_mb} MB)")
                    backup_log = log_path + ".1"
                    if os.path.exists(backup_log):
                        os.remove(backup_log)
                    shutil.copy2(log_path, backup_log)
                    
                    with open(log_path, 'w') as f:
                        f.write(f"--- Log rotacionado em {datetime.now()} ---\n")
            except Exception as e:
                logger.warning(f"Erro ao rotacionar log {log_path}: {e}")


def _backup_graph():
    """Cria backup do grafo antes de operações destrutivas com política de retenção inteligente."""
    if not os.path.isfile(agent_core.JSON_PATH):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Verifica espaço em disco antes do backup
    try:
        total, used, free = shutil.disk_usage(BACKUP_DIR)
        free_mb = free / (1024 * 1024)
        if free_mb < 500:
            logger.warning(f"Espaço em disco criticamente baixo para backups: {free_mb:.1f} MB livres.")
    except Exception as e:
        logger.warning(f"Não foi possível verificar espaço em disco: {e}")
        
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"obsidian_graph_{ts}.json")
    shutil.copy2(agent_core.JSON_PATH, backup_path)
    logger.info(f"Backup criado: {backup_path}")
    
    # Retenção configurável
    max_backups = int(os.getenv("FLOSE_MAX_BACKUPS", 5))
    size_limit_mb = float(os.getenv("FLOSE_BACKUP_SIZE_LIMIT_MB", 50.0))
    
    # 1. Filtra por quantidade máxima
    backups = sorted(
        [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith('.json')],
        key=os.path.getmtime,
        reverse=True
    )
    
    if len(backups) > max_backups:
        for old in backups[max_backups:]:
            try:
                os.remove(old)
                logger.info(f"Backup antigo removido por limite de contagem: {old}")
            except Exception as e:
                logger.warning(f"Erro ao remover backup antigo {old}: {e}")
        
        # Recarrega lista
        backups = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith('.json')],
            key=os.path.getmtime,
            reverse=True
        )
        
    # 2. Filtra por tamanho total acumulado de backups
    try:
        total_size = sum(os.path.getsize(b) for b in backups)
        while total_size > (size_limit_mb * 1024 * 1024) and len(backups) > 1:
            oldest = backups.pop()
            os.remove(oldest)
            logger.info(f"Backup antigo removido por limite de tamanho acumulado ({size_limit_mb} MB): {oldest}")
            total_size = sum(os.path.getsize(b) for b in backups)
    except Exception as e:
        logger.warning(f"Erro ao validar limite de tamanho de backups: {e}")
        
    return backup_path


def sanitize_graph():
    logger.info(f"Iniciando limpeza forense do grafo em {datetime.now()}")
    try:
        rotate_logs()
    except Exception as e:
        logger.warning(f"Erro ao rotacionar logs durante a higienização: {e}")
    _backup_graph()
    graph = load_graph()
    if not graph:
        logger.error("Grafo nao encontrado.")
        return

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # 1. Mapeamento de Super-Hubs para fusão
    ROOT_MAP = {
        "TECNOLOGIA": "tool_hub",
        "TECNOLOGIAS": "tool_hub",
        "TOOLS": "tool_hub",
        "TECH": "tool_hub",
        "TRABALHO": "work_hub",
        "WORK": "work_hub",
        "JOBS": "work_hub",
        "MBA": "mba_hub",
        "ACADEMICO": "mba_hub",
        "MBA EM IA": "mba_hub"
    }

    # 2. Identifica nós duplicados por título (mesmo tipo)
    unique_nodes = {}
    id_map = {} # Antigo ID -> Novo ID (para consertar edges)

    # Garante que os super-hubs existam e fiquem travados
    SUPER_HUBS = {"mestre", "mba_hub", "work_hub", "tool_hub", "classificar_hub"}
    
    new_nodes = []
    
    # Primeiro pass: Super-hubs e Mestre
    for node in nodes:
        if node["id"] in SUPER_HUBS:
            unique_nodes[node["id"]] = node
            new_nodes.append(node)
            id_map[node["id"]] = node["id"]

    # Segundo pass: Outros nós com fusão lógica
    for node in nodes:
        if node["id"] in SUPER_HUBS: continue
        
        n_id = node["id"]
        title = node.get("title", "").replace("📍", "").strip().upper()
        n_type = node.get("type", "classificar")

        # Regra de Super-Hub redundante
        if title in ROOT_MAP:
            id_map[n_id] = ROOT_MAP[title]
            logger.info(f"Fusao: Redirecionando '{n_id}' para '{ROOT_MAP[title]}'")
            continue

        # Chave de unicidade: TIPO + TÍTULO
        key = f"{n_type}_{title}"
        
        if key in unique_nodes:
            # Já existe um nó igual. Mapeia este ID para o ID do nó existente
            id_map[n_id] = unique_nodes[key]["id"]
            logger.info(f"Fusao: No duplicado '{n_id}' mesclado em '{id_map[n_id]}'")
        else:
            unique_nodes[key] = node
            id_map[n_id] = n_id
            new_nodes.append(node)

    # 3. Conserta as Edges (Redirecionamento de IDs e Deduplicação)
    new_edges = []
    seen_edges = set()

    for edge in edges:
        source = id_map.get(edge["source"], edge["source"])
        target = id_map.get(edge["target"], edge["target"])

        # Evita self-loops e duplicatas
        if source == target: continue
        
        edge_key = f"{source}_{target}"
        if edge_key not in seen_edges:
            edge["source"] = source
            edge["target"] = target
            new_edges.append(edge)
            seen_edges.add(edge_key)

    # 4. Limpeza de "Ghost Tools" órfãs que agora têm nós reais
    # (O id_map já deve ter cuidado de grande parte disso se os títulos baterem)

    # 5. Normalização de Depth (Opcional, mas ajuda no layout)
    # Root = 0, Super-hubs = 1, Resto = Automático (aqui mantemos o depth original para não quebrar o layout do D3)

    # 6. Salva o resultado
    status_msg = f"✅ Sanity Check concluído. {len(nodes)-len(new_nodes)} nós removidos."
    save_graph(new_nodes, new_edges, status_msg, overwrite=True)
    logger.info(f"Grafo curado! Nos: {len(new_nodes)} | Edges: {len(new_edges)}")

if __name__ == "__main__":
    sanitize_graph()
