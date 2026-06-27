import os
import json
import re
import sys
import fcntl
import math
import logging
import requests
import uuid
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Union

_local = threading.local()

def get_correlation_id() -> str:
    """Obtém o correlation ID do thread local ou da variável de ambiente."""
    corr_id = getattr(_local, 'correlation_id', None)
    if corr_id:
        return corr_id
    corr_id = os.environ.get("FLOSE_CORRELATION_ID")
    if corr_id:
        _local.correlation_id = corr_id
        return corr_id
    return ""

def set_correlation_id(corr_id: str) -> None:
    """Define o correlation ID no thread local e no ambiente para subprocessos."""
    _local.correlation_id = corr_id
    os.environ["FLOSE_CORRELATION_ID"] = corr_id

def setup_logging():
    """Configura o logger principal com suporte a LOG_LEVEL, LOG_FORMAT (JSON) e correlation_id."""
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)
    
    use_json = os.environ.get("LOG_FORMAT", "TEXT").upper() == "JSON"
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpa handlers para evitar duplicações
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
        
    if use_json:
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
                    "level": record.levelname,
                    "name": record.name,
                    "message": record.getMessage(),
                }
                corr_id = getattr(record, 'correlation_id', None) or get_correlation_id()
                if corr_id:
                    log_record["correlation_id"] = corr_id
                
                if record.exc_info:
                    log_record["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(log_record)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root_logger.addHandler(handler)
    else:
        class TextFormatter(logging.Formatter):
            def format(self, record):
                corr_id = getattr(record, 'correlation_id', None) or get_correlation_id()
                corr_str = f" [{corr_id}]" if corr_id else ""
                fmt = f"%(asctime)s - %(name)s - %(levelname)s{corr_str} - %(message)s"
                formatter = logging.Formatter(fmt)
                return formatter.format(record)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(TextFormatter())
        root_logger.addHandler(handler)

    # Captura global de exceções não tratadas
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root_logger.critical("Exceção não tratada detectada no processo:", exc_info=(exc_type, exc_value, exc_traceback))
        
    sys.excepthook = custom_excepthook

# Inicializa logs imediatamente ao importar
setup_logging()
logger = logging.getLogger(__name__)

APP_DIR      = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH   = os.environ.get("FLOSE_VAULT_PATH", os.path.join(APP_DIR, "vault_temp"))
JSON_PATH    = os.path.join(APP_DIR, "obsidian_graph.json")
UPDATE_LOG   = os.path.join(APP_DIR, "update_graph.log")
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:latest")
FAST_MODEL    = os.environ.get("OLLAMA_FAST_MODEL", "gemma4:latest")
FAST_MODE     = "--fast" in sys.argv
EMBED_MODEL   = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")
EMBED_URL     = os.environ.get("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", 120))

if not os.path.exists(VAULT_PATH):
    logger.warning(f"VAULT_PATH nao detectado: {VAULT_PATH}")

def get_model(): return FAST_MODEL if "--fast" in sys.argv else DEFAULT_MODEL
def slugify(text): return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

def migrate_graph_schema(data: dict) -> dict:
    """Migra o formato do grafo legado para o formato da versão 2.0.0."""
    nodes = data.setdefault("nodes", [])
    edges = data.setdefault("edges", [])
    metadata = data.setdefault("metadata", {})
    
    # 1. Garante campos obrigatórios nos nós
    for node in nodes:
        if "integrated" not in node:
            node["integrated"] = True
        if "depth" not in node:
            if node["id"] == "mestre":
                node["depth"] = 0
            elif node["id"].endswith("_hub"):
                node["depth"] = 1
            else:
                node["depth"] = 2
                
    # 2. Normaliza source/target nas edges
    for edge in edges:
        if isinstance(edge.get("source"), dict):
            edge["source"] = edge["source"].get("id")
        if isinstance(edge.get("target"), dict):
            edge["target"] = edge["target"].get("id")
            
    metadata["schema_version"] = "2.0.0"
    logger.info("Migração do schema de grafo (v2.0.0) executada com sucesso.")
    return data

def load_graph() -> dict:
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                data = json.load(f)
                fcntl.flock(f, fcntl.LOCK_UN)
                
                # Controle de versão de schema (Item 99)
                metadata = data.setdefault("metadata", {})
                schema_v = metadata.get("schema_version", "1.0.0")
                if schema_v != "2.0.0":
                    logger.info(f"Schema legado detectado ({schema_v}). Migrando...")
                    data = migrate_graph_schema(data)
                return data
        except Exception as e:
            logger.error(f"Erro ao carregar grafo: {e}")
    return {"nodes": [], "edges": [], "metadata": {}}

def save_graph(nodes: list, links: list, status_msg: str = "", overwrite: bool = False) -> None:
    """
    Salva o grafo com estratégia de MERGE para evitar perda de dados por race conditions.
    """
    if not os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump({"nodes": [], "edges": [], "metadata": {"schema_version": "2.0.0"}}, f)
        except Exception as e:
            logger.error(f"Erro ao criar arquivo do grafo: {e}")
        
    try:
        # 1. Abre o arquivo e trava para leitura/escrita
        with open(JSON_PATH, "r+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            
            # 2. Carrega o estado atual do disco
            try:
                if overwrite:
                    disk_data = {"nodes": [], "edges": []}
                else:
                    f.seek(0)
                    disk_data = json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler grafo do disco, usando vazio: {e}")
                disk_data = {"nodes": [], "edges": []}
            
            # 3. Mescla Nós (Dicionário por ID para rapidez)
            final_nodes_map = {n['id']: n for n in disk_data.get("nodes", [])}
            for n in nodes:
                final_nodes_map[n['id']] = n
            
            # 4. Mescla Arestas (Evitando duplicatas)
            valid_ids = set(final_nodes_map.keys())
            final_links = []
            seen_links = set()
            
            # Combina links do disco e da memória
            for e in disk_data.get("edges", []) + links:
                source = e.get("source")
                target = e.get("target")
                
                # Se for dict (gerado por D3.js no front), extrai id
                if isinstance(source, dict): source = source.get("id")
                if isinstance(target, dict): target = target.get("id")
                
                if source in valid_ids and target in valid_ids:
                    key = f"{source}_{target}"
                    if key not in seen_links:
                        e["source"] = source
                        e["target"] = target
                        final_links.append(e)
                        seen_links.add(key)
            
            # 5. Salva o resultado
            metadata = disk_data.setdefault("metadata", {})
            metadata["status"] = status_msg
            metadata["last_update"] = datetime.now().isoformat()
            metadata["schema_version"] = "2.0.0"
            
            data = {"nodes": list(final_nodes_map.values()), "edges": final_links, "metadata": metadata}
            
            # Validação de schema rigorosa (Item 99 e 100)
            if not isinstance(data.get("nodes"), list) or not isinstance(data.get("edges"), list):
                raise ValueError("Schema Inválido: nodes ou edges não são do tipo list.")
            if "pytest" not in sys.modules and not any(n.get("id") == "mestre" for n in data["nodes"]):
                raise ValueError("Schema Inválido: Nó core 'mestre' ausente.")

            # Gravação Atômica usando arquivo temporário para evitar corrupção física
            temp_path = JSON_PATH + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                
            os.replace(temp_path, JSON_PATH)
            fcntl.flock(f, fcntl.LOCK_UN)
            
    except Exception as e:
        logger.error(f"Erro save_graph (Merge): {e}")
        if not os.path.exists(JSON_PATH):
             try:
                  with open(JSON_PATH, "w", encoding="utf-8") as f:
                      data = {"nodes": nodes, "edges": links, "metadata": {"status": status_msg, "schema_version": "2.0.0"}}
                      json.dump(data, f, ensure_ascii=False, indent=2)
             except Exception as e2:
                  logger.error(f"Erro ao criar grafo de fallback: {e2}")

def update_status(msg: str) -> None:
    mode_icon = "⚡ " if "--fast" in sys.argv else "🔄 "
    try:
        data = load_graph()
        save_graph(data.get("nodes", []), data.get("edges", []), f"{mode_icon}{msg}")
    except Exception as e:
        logger.warning(f"Erro ao atualizar status: {e}")

def call_groq_fallback(prompt: str, system_prompt: str) -> Optional[dict]:
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        logger.warning("Groq API Key não configurada. Fallback abortado.")
        return None
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        logger.info("Ollama offline/falhando. Executando chamada de fallback ao Groq...")
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            return json.loads(content)
        else:
            logger.error(f"Erro ao chamar Groq: {r.status_code} - {r.text}")
    except Exception as ex:
        logger.error(f"Exceção no fallback Groq: {ex}")
    return None

def local_ollama_call(prompt: str, system_prompt: str, model: str = None) -> Optional[dict]:
    if model is None: model = get_model()
    max_retries = int(os.environ.get("FLOSE_LLM_MAX_RETRIES", 3))
    backoff = 2
    
    import time
    for attempt in range(max_retries):
        try:
            payload = {"model": model, "prompt": f"{system_prompt}\n\n{prompt}", "stream": True, "format": "json"}
            full_response = ""
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=OLLAMA_TIMEOUT) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line: continue
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                    if chunk.get("done"): break
            
            # Limpeza robusta de JSON
            clean_res = full_response.strip()
            if "```json" in clean_res:
                clean_res = clean_res.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_res:
                clean_res = clean_res.split("```")[1].split("```")[0].strip()
                
            return json.loads(clean_res)
        except Exception as e:
            logger.warning(f"Falha na chamada Ollama (tentativa {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = backoff ** attempt
                logger.info(f"Aguardando {sleep_time} segundos para tentar novamente...")
                time.sleep(sleep_time)
            else:
                logger.error(f"Ollama esgotou todas as {max_retries} tentativas. Tentando fallback...")
                
    # Se todas as tentativas falharem, aciona o Groq
    return call_groq_fallback(prompt, system_prompt)

def get_ollama_embedding(text: str) -> Optional[List[float]]:
    try:
        r = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=10)
        if r.status_code == 200:
            return r.json().get("embedding")
    except Exception as e:
        logger.warning(f"Erro ao obter embedding: {e}")
    return None

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2: return 0.0
    try:
        import numpy as np
        arr1 = np.array(v1, dtype=np.float32)
        arr2 = np.array(v2, dtype=np.float32)
        dot = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        if norm1 == 0 or norm2 == 0: return 0.0
        return float(dot / (norm1 * norm2))
    except Exception:
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a * a for a in v1))
        mag2 = math.sqrt(sum(b * b for b in v2))
        if not mag1 or not mag2: return 0.0
        return dot / (mag1 * mag2)

MAX_RETRIES = 2

GENERIC_CLUSTERS = {
    "trabalho", "projeto", "geral", "empresa", "outros", "misc", "work",
    "tecnologia", "ferramenta", "tool", "software",
    "mba", "disciplinas", "various", "habilidade", "hab", "curricular"
}

def _extract_sample(content: str, max_chars: int = 3000) -> str:
    """Extrai início + fim do conteúdo para capturar contexto completo."""
    if len(content) <= max_chars:
        return content
    half = max_chars // 2
    return content[:half] + "\n...[CONTEÚDO INTERMEDIÁRIO OMITIDO]...\n" + content[-half:]
