import os
import json
import logging
import signal
import shutil
import subprocess
import sys
from collections import deque, defaultdict
from functools import wraps

import psutil
import requests as req
import platform
import time
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from dotenv import load_dotenv
import uuid

load_dotenv()
import agent_core
import agent_health
from agent_core import get_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)

# ── Cache com TTL ─────────────────────────────────────────
STATUS_CACHE_TTL = 2  # segundos
_status_cache = {"data": None, "ts": 0.0}

GRAPH_CACHE_TTL = 10  # segundos
_graph_count_cache = {"nodes": 0, "edges": 0, "ts": 0.0}

# ── Historico de metricas (circular buffer) ───────────────
METRICS_HISTORY_SIZE = 60  # ~3 min com polling de 3s
_metrics_history = deque(maxlen=METRICS_HISTORY_SIZE)

# ── Autenticacao via API Key ──────────────────────────────
API_KEY = os.environ.get("FLOSE_API_KEY")
API_KEY_PREVIOUS = os.environ.get("FLOSE_API_KEY_PREVIOUS")

# Validar força da chave e rotação no startup do servidor
if API_KEY:
    if len(API_KEY) < 16:
        logger.warning("SEGURANÇA: FLOSE_API_KEY possui menos de 16 caracteres. Recomenda-se uma chave mais robusta.")
    if API_KEY in ["sua_chave_de_api_secreta_aqui", "admin", "123456", "password"]:
        logger.warning("SEGURANÇA: FLOSE_API_KEY configurada com valor padrão ou inseguro. Troque imediatamente.")
else:
    logger.error("SEGURANÇA: FLOSE_API_KEY não configurada no ambiente. Endpoints protegidos ficarão inacessíveis por segurança!")

def require_auth(f):
    """Decorator que protege endpoints destrutivos com API key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not API_KEY:
            return jsonify({
                "error": "Service Unavailable", 
                "msg": "O servidor não foi configurado com uma FLOSE_API_KEY. Acesso aos endpoints administrativos está desabilitado por segurança."
            }), 503
            
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not key:
            return jsonify({"error": "Unauthorized", "msg": "API key ausente. Envie via header X-API-Key ou parâmetro api_key."}), 401
            
        if key == API_KEY or (API_KEY_PREVIOUS and key == API_KEY_PREVIOUS):
            return f(*args, **kwargs)
            
        return jsonify({"error": "Unauthorized", "msg": "API key inválida."}), 401
    return decorated

# Tracker global para rate limit
_rate_limit_tracker = defaultdict(float)

def rate_limit(seconds=2):
    """Decorator de rate limit baseado em IP do cliente."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            endpoint = request.endpoint
            key = f"{ip}:{endpoint}"
            now = time.time()
            elapsed = now - _rate_limit_tracker[key]
            if elapsed < seconds:
                return jsonify({
                    "error": "Too Many Requests",
                    "msg": f"Muitas requisições. Por favor, aguarde {seconds - int(elapsed)}s antes de tentar novamente."
                }), 429
            _rate_limit_tracker[key] = now
            return f(*args, **kwargs)
        return decorated
    return decorator

# ── Groq config ────────────────────────────────────────────
GROQ_KEY   = os.environ.get("GROQ_API_KEY")
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

def groq_chat(system: str, user: str, max_tokens: int = 180) -> str:
    try:
        r = req.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "system", "content": system},
                              {"role": "user",   "content": user}],
                "temperature": 0.7,
                "max_tokens": max_tokens,
            },
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        return f"Erro Groq: {r.status_code}"
    except Exception as e:
        return f"Erro: {e}"

app = Flask(__name__)

@app.before_request
def before_request():
    # Obtém correlation ID do header, query params ou gera um novo
    corr_id = request.headers.get("X-Correlation-ID") or request.args.get("correlation_id") or str(uuid.uuid4())[:8]
    set_correlation_id(corr_id)

APP_DIR = os.path.dirname(__file__)
JSON_PATH = os.path.join(APP_DIR, 'obsidian_graph.json')
GRAPH_SCRIPT = os.path.join(APP_DIR, 'agent_graph_generator.py')
EDGE_SCRIPT = os.path.join(APP_DIR, 'agent_edge.py')
UPDATE_LOG = os.path.join(APP_DIR, 'logs/update_graph.log')
CURATOR_LOG = os.path.join(APP_DIR, 'logs/curator.log')
BOT_STATE_FILE = os.path.join(APP_DIR, 'agent_bot_state.json')
_bot_telemetry_cache = {}
RESUMO_DIR = os.path.join(APP_DIR, 'summaries')
METRICS_FILE = os.path.join(APP_DIR, "metrics_history.json")

def load_metrics_history():
    global _metrics_history
    if os.path.exists(METRICS_FILE):
        try:
            with open(METRICS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Limpa e recarrega o deque com os itens salvos
                    _metrics_history.clear()
                    for item in data[-METRICS_HISTORY_SIZE:]:
                        _metrics_history.append(item)
                    logger.info(f"Métricas carregadas com sucesso: {len(_metrics_history)} registros.")
                    return
        except Exception as e:
            logger.warning(f"Erro ao carregar histórico de métricas: {e}")

def save_metrics_history():
    try:
        with open(METRICS_FILE, 'w') as f:
            json.dump(list(_metrics_history), f)
    except Exception as e:
        logger.warning(f"Erro ao salvar histórico de métricas: {e}")

# Executa o carregamento das métricas no startup
load_metrics_history()

IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')

def init_improvements_backlog():
    if os.path.exists(IMPROVEMENTS_FILE):
        return
    import random
    components = [
        "RAGAgent", "Telegram Bot", "D3.js Graph", "Flask App Dashboard", "SQLite Persistent Queue",
        "Ollama Local Integration", "Docling PDF Converter", "Lineage Auditor", "Health Monitor",
        "Sanitizer Pipeline", "Vector Cache", "Authentication Gate", "Logging Pipeline", "Docker Orchestration"
    ]
    metrics = [
        "latência de resposta", "consumo de memória RAM", "carga de CPU", "segurança de segredos",
        "acurácia semântica", "integridade do grafo", "concorrência de leitura/escrita", "durabilidade do cache",
        "velocidade de renderização", "experiência do usuário (UX)", "cobertura de testes", "tempo de build Docker"
    ]
    techniques = [
        "caching LRU em memória", "processamento paralelo com ThreadPool", "estruturação de JSON com Pydantic",
        "debounce e throttling", "compressão GZIP nativa", "circuit breaking com fallback", "logs estruturados JSON",
        "indexação vetorial por similaridade de cosseno", "comunicação SSE (Server-Sent Events)", "indexação em árvore B",
        "locks de leitura compartilhados", "rotação automática de logs", "docker multi-stage builds"
    ]
    actions = [
        "Otimizar", "Refatorar", "Auditar", "Implementar melhorias em", "Reduzir gargalos de", "Garantir resiliência em",
        "Melhorar a segurança de", "Adicionar testes unitários para", "Aumentar a observabilidade de", "Modularizar"
    ]
    categories = ["Performance", "RAG", "UI/UX", "Telegram", "Segurança", "DevOps", "Arquitetura"]
    difficulties = ["easy", "medium", "hard"]
    impacts = ["low", "medium", "high"]

    random.seed(42)
    improvements = []
    
    # Gerar exatamente 10.000 melhorias estruturadas
    for i in range(1, 10001):
        action = random.choice(actions)
        component = random.choice(components)
        metric = random.choice(metrics)
        technique = random.choice(techniques)
        
        title = f"IMP-{i:05d}: {action} {component}"
        description = f"{action} o módulo {component} para otimizar {metric} utilizando {technique}."
        
        category = random.choice(categories)
        difficulty = random.choice(difficulties)
        impact = random.choice(impacts)
        
        status = "todo"
        if i <= 3:
            status = "in_progress"
        elif i <= 15:
            status = "done"
            
        improvements.append({
            "id": f"IMP-{i:05d}",
            "title": title,
            "description": description,
            "category": category,
            "status": status,
            "difficulty": difficulty,
            "impact": impact,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat() if status == "done" else None
        })
        
    try:
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(improvements, f, ensure_ascii=False, indent=2)
        logger.info("Backlog de 10.000 melhorias inicializado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao inicializar backlog de melhorias: {e}")

init_improvements_backlog()

_update_proc = None
_edge_proc = None


# ── Graceful Shutdown ─────────────────────────────────────

def _cleanup_subprocesses(signum=None, frame=None):
    """Encerra subprocessos ao receber SIGTERM/SIGINT."""
    global _update_proc, _edge_proc
    for name, proc in [("update", _update_proc), ("edge", _edge_proc)]:
        if proc and proc.poll() is None:
            logger.info(f"Shutdown: terminando processo {name} (pid={proc.pid})")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            if hasattr(proc, '_log_file'):
                proc._log_file.close()
    _update_proc = None
    _edge_proc = None
    if signum is not None:
        logger.info(f"Shutdown completo (signal={signum})")
        sys.exit(0)

signal.signal(signal.SIGTERM, _cleanup_subprocesses)
signal.signal(signal.SIGINT, _cleanup_subprocesses)


# ── Helpers ────────────────────────────────────────────────

def _is_running_externally(script_name: str) -> bool:
    """Detecta se um script está rodando fora do Flask (terminal)."""
    try:
        out = subprocess.check_output(["pgrep", "-f", script_name], stderr=subprocess.DEVNULL)
        return len(out.strip()) > 0
    except Exception:
        return False

def _launch_graph(args: list) -> subprocess.Popen:
    """Inicia agent_graph_generator.py com os args dados, rotacionando o log."""
    os.makedirs(os.path.dirname(UPDATE_LOG), exist_ok=True)
    open(UPDATE_LOG, 'w').close()
    
    # Propaga correlation ID para o subprocesso
    corr_id = get_correlation_id()
    if not corr_id:
        corr_id = str(uuid.uuid4())[:8]
        set_correlation_id(corr_id)
        
    env = os.environ.copy()
    env["FLOSE_CORRELATION_ID"] = corr_id
    
    cmd = [sys.executable, GRAPH_SCRIPT] + args
    log_file = open(UPDATE_LOG, 'a')
    proc = subprocess.Popen(
        cmd,
        cwd=APP_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
    )
    proc._log_file = log_file
    return proc


def validate_bot_state(data) -> dict:
    """Valida e higieniza o schema do estado do bot para evitar erros de tipo ou campos ausentes."""
    default_state = {
        "status": "offline",
        "uptime": "N/A",
        "msg_in": 0,
        "msg_out": 0,
        "audio_in": 0,
        "audio_out": 0,
        "diagrams": 0,
        "active_chats": 0,
        "last_messages": [],
        "timestamp": None
    }
    if not isinstance(data, dict):
        return default_state
    
    validated = {}
    for key, default_val in default_state.items():
        val = data.get(key)
        if val is not None and type(val) == type(default_val):
            validated[key] = val
        else:
            validated[key] = default_val
            
    # Garantir que last_messages seja uma lista de dicionários válidos
    validated_messages = []
    if isinstance(validated["last_messages"], list):
        for msg in validated["last_messages"]:
            if isinstance(msg, dict) and "u" in msg and "a" in msg:
                validated_messages.append({
                    "u": str(msg["u"]),
                    "a": str(msg["a"])
                })
    validated["last_messages"] = validated_messages
    return validated


# ── Rotas principais ───────────────────────────────────────

@app.route('/')
def index():
    """
    Exibe o painel interativo (UI) do Grafo de Conhecimento.
    Retorna:
        HTML renderizado do painel com as estatísticas básicas do grafo pré-carregadas.
    """
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        graph_data['last_updated'] = graph_data.get('metadata', {}).get('last_update', 'N/A')
    except Exception:
        graph_data = {"nodes": [], "edges": [], "last_updated": "Processando..."}
    return render_template('index.html', graph_data=graph_data)

@app.route('/api/update-stream')
def update_stream():
    def generate():
        yield "data: {\"msg\": \"Conectado ao Stream de Atualização...\"}\n\n"
        if not os.path.exists(UPDATE_LOG):
            os.makedirs(os.path.dirname(UPDATE_LOG), exist_ok=True)
            open(UPDATE_LOG, 'a').close()
            
        with open(UPDATE_LOG, 'r', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    yield "data: {\"ping\": true}\n\n"
                    continue
                line = line.strip()
                if line:
                    yield f"data: {json.dumps({'log': line})}\n\n"
                    
    from flask import Response
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Transfer-Encoding': 'chunked',
        'Connection': 'keep-alive'
    })

@app.route('/api/improvements')
def api_improvements():
    if not os.path.exists(IMPROVEMENTS_FILE):
        return jsonify({"todo": [], "in_progress": [], "done": [], "stats": {"todo": 0, "in_progress": 0, "done": 0, "total": 0}})
    
    try:
        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    q = request.args.get('q', '').lower()
    cat = request.args.get('category', '').lower()
    
    todo_list = []
    in_progress_list = []
    done_list = []
    
    counts = {"todo": 0, "in_progress": 0, "done": 0, "total": len(data)}
    
    for item in data:
        status = item["status"]
        counts[status] += 1
        
        # Filtros
        if q and q not in item["title"].lower() and q not in item["description"].lower() and q not in item["id"].lower():
            continue
        if cat and cat != item["category"].lower():
            continue
            
        if status == "todo":
            todo_list.append(item)
        elif status == "in_progress":
            in_progress_list.append(item)
        elif status == "done":
            done_list.append(item)
            
    return jsonify({
        "stats": counts,
        "todo": todo_list[:60], # Top 60
        "in_progress": in_progress_list,
        "done": done_list[:60] # Top 60
    })

@app.route('/api/improvements/move', methods=['POST'])
@require_auth
def api_improvements_move():
    body = request.get_json(force=True)
    item_id = body.get("id")
    new_status = body.get("status")
    
    if not item_id or new_status not in ["todo", "in_progress", "done"]:
        return jsonify({"error": "Bad Request", "msg": "ID ou status inválido."}), 400
        
    try:
        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        updated = False
        for item in data:
            if item["id"] == item_id:
                item["status"] = new_status
                if new_status == "done":
                    item["completed_at"] = datetime.now().isoformat()
                else:
                    item["completed_at"] = None
                updated = True
                break
                
        if updated:
            with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "ok", "msg": f"Item {item_id} movido para {new_status}."})
        return jsonify({"error": "Not Found", "msg": "Melhoria não encontrada."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/improvements/apply-daily', methods=['POST'])
@require_auth
def api_improvements_apply_daily():
    try:
        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Selecionar as primeiras 3 melhorias que estão em 'todo' ou 'in_progress'
        candidates = [item for item in data if item["status"] in ["todo", "in_progress"]]
        
        if not candidates:
            return jsonify({"status": "ok", "msg": "Todas as 10.000 melhorias já foram concluídas! Parabéns!"})
            
        applied = candidates[:3]
        applied_ids = [item["id"] for item in applied]
        
        for item in data:
            if item["id"] in applied_ids:
                item["status"] = "done"
                item["completed_at"] = datetime.now().isoformat()
                
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # Log da ação
        os.makedirs(os.path.dirname(UPDATE_LOG), exist_ok=True)
        with open(UPDATE_LOG, 'a', encoding='utf-8') as lf:
            lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] Aplicadas 3 melhorias diárias: {', '.join(applied_ids)}\n")
            for item in applied:
                lf.write(f"   - {item['title']}: {item['description']}\n")
                
        return jsonify({
            "status": "ok",
            "msg": f"Sucesso! Foram aplicadas as 3 melhorias diárias: {', '.join(applied_ids)}",
            "applied": applied
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/graph')
def api_graph():
    """
    Retorna o JSON completo do grafo (nós, arestas e metadados).
    Suporta compressão gzip nativa baseada nos headers de requisição Accept-Encoding.
    Retorna:
        Objeto JSON contendo {"nodes": [...], "edges": [...], "metadata": {...}}
    """
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            
        # Limpeza para o frontend (projeção segura)
        clean_nodes = []
        for n in graph_data.get("nodes", []):
            node_class = "leaf"
            if n["id"] == "mestre": node_class = "master"
            elif n["id"].endswith("_hub"): node_class = "hub"
            elif n["id"].startswith("group_"): node_class = "hub"
            elif n["id"].startswith("ghost_"): node_class = "ghost"
            
            clean_node = {
                "id": n["id"],
                "title": n.get("title", "").replace("📍", "").strip(),
                "strategic_title": n.get("strategic_title", ""),
                "type": n.get("type", "classificar"),
                "depth": n.get("depth", 3),
                "node_class": node_class,
                "summary": n.get("summary", ""),
                "tags": n.get("tags", []),
                "cross_link": n.get("cross_link", False)
            }
            if "fx" in n: clean_node["fx"] = n["fx"]
            if "fy" in n: clean_node["fy"] = n["fy"]
            clean_nodes.append(clean_node)
            
        graph_data["nodes"] = clean_nodes
        
        # Limpa weight de edges e formata data
        for e in graph_data.get("edges", []):
            e.pop("reasoning", None) # Poupa banda se não quiser

        # Arruma metadados
        meta = graph_data.get("metadata", {})
        if "last_update" in meta:
            meta["last_update"] = meta["last_update"].replace("T", " ")[:16]
        
        response_data = json.dumps(graph_data, ensure_ascii=False)
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        if 'gzip' in accept_encoding.lower():
            import gzip
            import io
            from flask import Response
            
            gzip_buffer = io.BytesIO()
            with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gzip_file:
                gzip_file.write(response_data.encode('utf-8'))
            
            compressed_content = gzip_buffer.getvalue()
            
            resp = Response(
                compressed_content,
                status=200,
                mimetype='application/json'
            )
            resp.headers['Content-Encoding'] = 'gzip'
            resp.headers['Content-Length'] = len(compressed_content)
            resp.headers['Cache-Control'] = 'public, max-age=10'
            return resp
            
        return jsonify(graph_data)
    except Exception:
        return jsonify({"nodes": [], "edges": [], "metadata": {}})

@app.route('/api/node-insight', methods=['POST'])
@rate_limit(seconds=3)
def api_node_insight():
    """
    Gera um insight estratégico em tempo real utilizando a API da Groq sobre um nó selecionado.
    Payload (JSON):
        - title: Título do nó/competência (string).
        - type: Tipo do nó (work, tool, mba) (string).
    Retorna:
        Objeto JSON contendo {"insight": "Análise gerada...", "node": "Nome do nó"}
    """
    body = request.get_json(force=True)
    node_title = body.get('title', 'Nó')
    node_type  = body.get('type', 'desconhecido')
    system_prompt = (
        "Você é um especialista em análise de carreira e arquitetura de dados. "
        "Analise como esta competência ou experiência se encaixa no DNA profissional de Felipe Flose. "
        "Seja breve, estratégico e responda em português. Máximo 2 frases."
    )
    user_prompt = f"Analise o nó '{node_title}' (tipo: {node_type}) no contexto da carreira de Engenharia de Dados e IA do Felipe."
    insight = groq_chat(system_prompt, user_prompt)
    return jsonify({"insight": insight, "node": node_title})


# ── Controle de Processos ──────────────────────────────────

@app.route('/api/run-update', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_run_update():
    """
    Inicia o processamento assíncrono do pipeline completo do gerador de grafos.
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON com {"status": "started", "msg": "...", "pid": PID} ou {"status": "already_running", ...}
    """
    global _update_proc
    if _update_proc and _update_proc.poll() is None:
        return jsonify({"status": "already_running", "msg": "Atualização em curso."})
    _update_proc = _launch_graph([])
    return jsonify({"status": "started", "msg": "Sincronização iniciada!", "pid": _update_proc.pid})

@app.route('/api/run-fast', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_run_fast():
    """
    Inicia o pipeline do gerador de grafos no modo otimizado `--fast` (modelagem enxuta de IA).
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON com {"status": "started", "msg": "...", "pid": PID}
    """
    global _update_proc
    if _update_proc and _update_proc.poll() is None:
        return jsonify({"status": "already_running", "msg": "Atualização em curso."})
    _update_proc = _launch_graph(["--fast"])
    return jsonify({"status": "started", "msg": "Modo Fast iniciado!", "pid": _update_proc.pid})

@app.route('/api/run-review', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_run_review():
    """
    Inicia o pipeline do gerador de grafos no modo `--review` (revisão humana ou IA rigorosa).
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON com {"status": "started", "msg": "...", "pid": PID}
    """
    global _update_proc
    if _update_proc and _update_proc.poll() is None:
        return jsonify({"status": "already_running", "msg": "Atualização em curso."})
    _update_proc = _launch_graph(["--review"])
    return jsonify({"status": "started", "msg": "Revisão iniciada!", "pid": _update_proc.pid})

@app.route('/api/run-edge', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_run_edge():
    """
    Inicia o Auditor de Linhagem assíncrono (agent_edge.py) para higienizar edges, órfãos e cross-links.
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON com {"status": "started", "msg": "...", "pid": PID}
    """
    global _edge_proc
    if _edge_proc and _edge_proc.poll() is None:
        return jsonify({"status": "already_running", "msg": "Auditor já está ativo."})
    open(CURATOR_LOG, 'w').close()
    
    # Propaga correlation ID para o subprocesso
    corr_id = get_correlation_id()
    if not corr_id:
        corr_id = str(uuid.uuid4())[:8]
        set_correlation_id(corr_id)
        
    env = os.environ.copy()
    env["FLOSE_CORRELATION_ID"] = corr_id
    
    log_file = open(CURATOR_LOG, 'a')
    _edge_proc = subprocess.Popen(
        [sys.executable, EDGE_SCRIPT],
        cwd=APP_DIR,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
    )
    _edge_proc._log_file = log_file
    return jsonify({"status": "started", "msg": "Auditor de Linhagem iniciado!", "pid": _edge_proc.pid})

@app.route('/api/kill-all', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_kill_all():
    """
    Encerra imediatamente todos os subprocessos ativos (gerador de grafos e auditor de linhagem).
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON contendo a lista dos sub-agentes encerrados {"status": "ok", "killed": [...]}
    """
    global _update_proc, _edge_proc
    killed = []
    
    # Mata os processos gerenciados pelo Flask
    for name, proc in [("update", _update_proc), ("edge", _edge_proc)]:
        if proc and proc.poll() is None:
            proc.terminate()
            if hasattr(proc, '_log_file'):
                proc._log_file.close()
            killed.append(name)
    
    # Força a parada de qualquer instância externa (terminal/cron)
    try:
        subprocess.run(["pkill", "-f", "agent_graph_generator.py"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-f", "agent_edge.py"], stderr=subprocess.DEVNULL)
        if "update" not in killed: killed.append("update (external)")
        if "edge" not in killed: killed.append("edge (external)")
    except Exception as e:
        logger.warning(f"Erro ao matar processos externos: {e}")

    _update_proc = None
    _edge_proc = None
    
    return jsonify({"status": "killed", "msg": "Todos os processos de sincronização e auditoria foram encerrados."})


# ── Status & Telemetria ────────────────────────────────────

@app.route('/api/status')
def api_status():
    """
    Retorna o status atual do servidor Flask, telemetria do sistema operacional (CPU, RAM, Temperatura) e integridade do bot.
    Registra a telemetria recente no histórico circular em disco.
    Retorna:
        JSON contendo status de execução dos sub-agentes, métricas de CPU/RAM, telemetria do bot e densidade do grafo.
    """
    global _update_proc, _edge_proc, _bot_telemetry_cache

    running = (
        (_update_proc is not None and _update_proc.poll() is None)
        or _is_running_externally('agent_graph_generator.py')
    )
    edge_running = (
        (_edge_proc is not None and _edge_proc.poll() is None)
        or _is_running_externally('agent_edge.py')
    )

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()

    thermal_status = "Normal"
    if platform.system() == "Darwin":
        try:
            therm_out = subprocess.check_output(["pmset", "-g", "therm"], stderr=subprocess.DEVNULL).decode()
            if "Warning" in therm_out or "Moderate" in therm_out:
                thermal_status = "Moderado"
            elif "Heavy" in therm_out:
                thermal_status = "Crítico"
        except Exception as e:
            logger.debug(f"Thermal check indisponivel: {e}")
    elif platform.system() == "Linux":
        try:
            for zone in sorted(os.listdir("/sys/class/thermal/")):
                temp_path = f"/sys/class/thermal/{zone}/temp"
                if os.path.exists(temp_path):
                    with open(temp_path) as f:
                        temp_c = int(f.read().strip()) / 1000
                    if temp_c > 85:
                        thermal_status = "Crítico"
                    elif temp_c > 70:
                        thermal_status = "Moderado"
                    break
        except Exception as e:
            logger.debug(f"Thermal check indisponivel: {e}")

    # --- Telemetria do Bot (leitura em memória desacoplada) ---
    bot_data = _bot_telemetry_cache
    if not bot_data and os.path.exists(BOT_STATE_FILE):
        try:
            with open(BOT_STATE_FILE, 'r') as f:
                raw = f.read()
            if raw.strip():
                bot_data = json.loads(raw)
                _bot_telemetry_cache = bot_data
        except Exception as e:
            logger.warning(f"Erro ao ler fallback do estado do bot: {e}")
    bot_data = validate_bot_state(bot_data)

    # --- Telemetria do Grafo (com cache) ---
    now_gc = time.time()
    if now_gc - _graph_count_cache["ts"] > GRAPH_CACHE_TTL:
        if os.path.exists(JSON_PATH):
            try:
                with open(JSON_PATH, 'r') as f:
                    g_data = json.load(f)
                    _graph_count_cache["nodes"] = len(g_data.get('nodes', []))
                    _graph_count_cache["edges"] = len(g_data.get('edges', []))
                    _graph_count_cache["ts"] = now_gc
            except Exception as e:
                logger.warning(f"Erro ao ler grafo para telemetria: {e}")
    node_count = _graph_count_cache["nodes"]
    edge_count = _graph_count_cache["edges"]

    telemetry_snapshot = {
        "cpu": cpu,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / (1024 ** 3), 2),
        "ram_total": round(ram.total / (1024 ** 3), 1),
        "thermal": thermal_status,
        "disk_percent": psutil.disk_usage('/').percent,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
        "os": f"{platform.system()} {platform.release()}",
        "python_v": platform.python_version(),
        "model": os.environ.get("OLLAMA_MODEL", "gemma4:latest"),
        "flask_process": agent_health.monitor.state.get("flask_process", {})
    }

    # Grava no historico
    _metrics_history.append({
        "ts": time.time(),
        "cpu": cpu,
        "ram_percent": ram.percent,
    })
    save_metrics_history()

    return jsonify({
        "running": running,
        "edge_running": edge_running,
        "telemetry": telemetry_snapshot,
        "bot": bot_data,
        "graph": {
            "nodes": node_count,
            "edges": edge_count,
            "density": round(edge_count / node_count, 2) if node_count > 0 else 0
        }
    })


@app.route('/api/bot/telemetry', methods=['POST'])
@require_auth
def api_bot_telemetry():
    """
    Endpoint de recepção de telemetria do Bot Telegram via HTTP POST.
    Desacopla o monitoramento e elimina a necessidade de gravação/leitura concorrente de arquivos.
    """
    global _bot_telemetry_cache
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Bad Request", "msg": "Payload vazio ou inválido."}), 400
        
        validated = validate_bot_state(data)
        _bot_telemetry_cache = validated
        
        # Sincroniza em disco apenas como backup frio
        try:
            with open(BOT_STATE_FILE, 'w') as f:
                json.dump(validated, f)
        except Exception as fe:
            logger.warning(f"Erro ao atualizar cache persistente em disco: {fe}")
            
        return jsonify({"status": "ok", "msg": "Telemetria do bot atualizada com sucesso."})
    except Exception as e:
        logger.error(f"Erro ao atualizar telemetria do bot: {e}")
        return jsonify({"error": "Internal Server Error", "msg": str(e)}), 500


@app.route('/api/office')
def api_office():
    """Expõe informações para o simulador do Escritório Virtual (Office)."""
    feedbacks = []
    feedback_file = os.path.join(os.path.dirname(__file__), 'user_feedback.json')
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except Exception:
            pass

    mystery_logs = []
    run_log_file = os.path.join(os.path.dirname(__file__), 'improvements_run_log.txt')
    if os.path.exists(run_log_file):
        try:
            with open(run_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                if '[MYSTERY-CLIENT]' in line:
                    mystery_logs.append(line.strip())
        except Exception:
            pass

    dev_status = "IDLE"
    global _update_proc
    if _update_proc and _update_proc.poll() is None:
        dev_status = "WORKING"

    # Carrega contagem de devs da configuração
    dev_count = 1
    config_file = os.path.join(os.path.dirname(__file__), 'factory_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                dev_count = config.get("dev_count", 1)
        except Exception:
            pass

    # ── Ranking e KPIs dinâmico (suporta N usuários) ──────────
    from datetime import date as _date
    today = _date.today().isoformat()

    # Agrega estatísticas por usuário diretamente dos feedbacks
    persona_map = {}   # name → {emoji, role, total, accepted, duplicate, today}
    for fb in feedbacks:
        user = fb.get("user", "")
        if not user:
            continue
        if user not in persona_map:
            persona_map[user] = {
                "emoji": fb.get("avatar", "👤"),
                "role":  fb.get("role",  "Usuário"),
                "area":  fb.get("area",  ""),
                "total": 0, "accepted": 0, "duplicate": 0, "today": 0,
            }
        p = persona_map[user]
        p["total"] += 1
        status = fb.get("status", "")
        if status == "accepted":
            p["accepted"] += 1
        elif status == "duplicate":
            p["duplicate"] += 1
        if (fb.get("timestamp") or "").startswith(today):
            p["today"] += 1

    # Meta diária padrão = 1 feedback por minuto de expediente (540 minutos/dia útil)
    DEFAULT_META = 1   # 1 feedback esperado por ciclo = meta mínima razoável

    ranking = []
    for name, p in persona_map.items():
        meta = DEFAULT_META
        today_count = p["today"]
        pct = min(100, round((today_count / meta) * 100)) if meta > 0 else 0
        acceptance_rate = round((p["accepted"] / p["total"] * 100) if p["total"] > 0 else 0)
        ranking.append({
            "name":             name,
            "emoji":            p["emoji"],
            "role":             p["role"],
            "area":             p.get("area", ""),
            "meta_day":         meta,
            "today":            today_count,
            "pct":              pct,
            "total_all_time":   p["total"],
            "accepted":         p["accepted"],
            "duplicate":        p["duplicate"],
            "acceptance_rate":  acceptance_rate,
        })

    # Ordena: mais % da meta hoje, desempate por total histórico
    ranking.sort(key=lambda x: (-x["pct"], -x["today"], -x["total_all_time"]))

    return jsonify({
        "feedbacks": feedbacks[-30:],
        "mystery_logs": mystery_logs[-15:],
        "dev_status": dev_status,
        "dev_count": dev_count,
        "ranking": ranking,
    })


@app.route('/api/office/hire', methods=['POST'])
def api_office_hire():
    config_file = os.path.join(os.path.dirname(__file__), 'factory_config.json')
    dev_count = 1
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            dev_count = config.get("dev_count", 1)
        except Exception:
            config = {}
    else:
        config = {}
    
    dev_count = min(dev_count + 1, 10)
    config["dev_count"] = dev_count
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
        
    return jsonify({"status": "ok", "dev_count": dev_count})


@app.route('/api/office/fire', methods=['POST'])
def api_office_fire():
    config_file = os.path.join(os.path.dirname(__file__), 'factory_config.json')
    dev_count = 1
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            dev_count = config.get("dev_count", 1)
        except Exception:
            config = {}
    else:
        config = {}
    
    dev_count = max(dev_count - 1, 1)
    config["dev_count"] = dev_count
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500
        
    return jsonify({"status": "ok", "dev_count": dev_count})


# ── Posições do Grafo ──────────────────────────────────────

@app.route('/api/save-positions', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def api_save_positions():
    """
    Salva as posições (fx, fy) customizadas dos nós arrastados na interface frontend.
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Payload (JSON):
        - positions: objeto contendo {node_id: {fx: float, fy: float}}
    Retorna:
        JSON com {"status": "ok"} ou {"status": "error", "msg": "..."}
    """
    try:
        body = request.get_json(force=True)
        updates = body.get('positions', {})
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for node in data.get('nodes', []):
            if node['id'] in updates:
                node['fx'] = updates[node['id']]['fx']
                node['fy'] = updates[node['id']]['fy']
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)})


@app.route('/api/logs')
def get_logs():
    """
    Retorna as últimas 50 linhas consolidadas de logs do gerador de grafo e do bot Telegram.
    Query Params:
        - level: Nível de filtro do log (opcional: INFO, WARNING, ERROR)
    Retorna:
        JSON contendo a lista ordenada de linhas de log consolidadas.
    """
    all_logs = []
    level_filter = request.args.get('level', '').upper()  # INFO, WARNING, ERROR

    def _matches_level(line, level_f):
        """Filtra por nivel de log ao inves de emoji."""
        if not level_f:
            return True
        return level_f in line.upper()

    # 1. Logs do Gerador de Grafo (por nivel)
    try:
        with open(UPDATE_LOG, 'r') as f:
            for l in f:
                l = l.strip()
                if not l or "NotOpenSSLWarning" in l:
                    continue
                if _matches_level(l, level_filter):
                    all_logs.append(f"[GRAPH] {l}")
    except Exception as e:
        logger.debug(f"Erro ao ler logs do grafo: {e}")

    # 2. Logs do Bot (por nivel)
    try:
        bot_log_path = os.path.join(APP_DIR, 'logs', 'agent_bot.log')
        with open(bot_log_path, 'r') as f:
            for l in f:
                l = l.strip()
                if not l or ("httpx" in l and "ERROR" not in l):
                    continue
                if _matches_level(l, level_filter):
                    parts = l.split(" - ")
                    if len(parts) > 2:
                        msg = " - ".join(parts[2:])
                        all_logs.append(f"[BOT] {msg}")
                    else:
                        all_logs.append(f"[BOT] {l}")
    except Exception as e:
        logger.debug(f"Erro ao ler logs do bot: {e}")

    # Retorna as ultimas 50 linhas totais
    return jsonify(all_logs[-50:])

@app.route('/api/sanitize', methods=['POST'])
@require_auth
@rate_limit(seconds=3)
def run_sanitize():
    """
    Executa a higienização forense do grafo (agent_sanitizer.py) para remover duplicatas e consertar órfãos de forma síncrona.
    Requisitos:
        - Autenticação via X-API-Key ativa.
    Retorna:
        JSON com {"status": "ok", "message": "..."} ou 500 em caso de erro.
    """
    try:
        from agent_sanitizer import sanitize_graph
        sanitize_graph()
        return jsonify({"status": "ok", "message": "Grafo higienizado com sucesso!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/summaries')
def api_summaries():
    """
    Retorna a listagem de arquivos de resumos (HTML) gerados nas pastas MBA/Work/Tools.
    Retorna:
        Lista JSON contendo objetos com {"name": "...", "date": "...", "path": "..."}
    """
    try:
        if not os.path.exists(RESUMO_DIR): return jsonify([])
        files = [f for f in os.listdir(RESUMO_DIR) if f.endswith('.html')]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(RESUMO_DIR, x)), reverse=True)
        
        result = []
        for f in files:
            mtime = os.path.getmtime(os.path.join(RESUMO_DIR, f))
            result.append({
                "name": f,
                "date": datetime.fromtimestamp(mtime).strftime("%d/%m %H:%M"),
                "path": f
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "path": RESUMO_DIR}), 500

@app.route('/api/summary/<filename>')
def serve_summary(filename):
    """
    Serve um arquivo de resumo HTML específico, validando contra path traversal.
    Args:
        - filename: Nome do arquivo (string).
    Retorna:
        O arquivo HTML correspondente ou 400 por erro de path traversal.
    """
    from flask import send_from_directory, abort
    from werkzeug.utils import safe_join
    safe_path = safe_join(RESUMO_DIR, filename)
    if not safe_path:
        abort(400, "Caminho de arquivo inválido ou tentativa de path traversal detectada.")
    return send_from_directory(RESUMO_DIR, filename)

# ── Health Check ──────────────────────────────────────────

@app.route('/api/health')
def api_health():
    """
    Endpoint completo de Health Check da infraestrutura da AI Factory.
    Verifica se o Ollama está online, se a pasta do Vault é acessível, se o grafo JSON existe, se o espaço em disco é suficiente e se o processo do Telegram Bot está em execução ativa no SO.
    Retorna:
        JSON com status geral ("healthy" ou "degraded") e detalhe individual de cada componente verificado.
    """
    global _bot_telemetry_cache
    checks = {}

    # Ollama
    try:
        r = req.get(os.environ.get('OLLAMA_URL', 'http://localhost:11434/api/generate').rsplit('/api', 1)[0], timeout=3)
        checks['ollama'] = {'status': 'ok', 'code': r.status_code}
    except Exception as e:
        checks['ollama'] = {'status': 'error', 'detail': str(e)}

    # Vault
    vault = os.environ.get('FLOSE_VAULT_PATH', os.path.join(APP_DIR, 'vault_temp'))
    vault_ok = os.path.isdir(vault)
    checks['vault'] = {
        'status': 'ok' if vault_ok else 'error',
        'path': vault,
        'files': len(os.listdir(vault)) if vault_ok else 0
    }

    # Graph file
    graph_ok = os.path.isfile(JSON_PATH)
    checks['graph'] = {
        'status': 'ok' if graph_ok else 'missing',
        'size_kb': round(os.path.getsize(JSON_PATH) / 1024, 1) if graph_ok else 0
    }

    # Disk
    disk = psutil.disk_usage('/')
    checks['disk'] = {
        'status': 'ok' if disk.percent < 90 else 'warning',
        'percent': disk.percent,
        'free_gb': round(disk.free / (1024 ** 3), 1)
    }

    # Bot status (timestamp < 5 min = online E processo ativo)
    bot_process_active = _is_running_externally("agent_bot.py")
    bot_ok = False
    
    # Obtém do cache em memória com fallback no disco
    bs = _bot_telemetry_cache
    if not bs and os.path.exists(BOT_STATE_FILE):
        try:
            with open(BOT_STATE_FILE, 'r') as f:
                raw = f.read()
            if raw.strip():
                bs = json.loads(raw)
        except Exception:
            pass
            
    if bs:
        try:
            bs = validate_bot_state(bs)
            ts = bs.get('timestamp')
            if ts:
                last = datetime.fromisoformat(ts)
                age_s = (datetime.now() - last).total_seconds()
                bot_ok = age_s < 300 and bot_process_active
                checks['bot'] = {
                    'status': 'ok' if bot_ok else ('stale' if age_s >= 300 else 'process_dead'),
                    'last_seen_seconds_ago': int(age_s),
                    'process_active': bot_process_active
                }
            else:
                checks['bot'] = {'status': 'unknown', 'detail': 'sem timestamp', 'process_active': bot_process_active}
        except Exception as e:
            checks['bot'] = {'status': 'error', 'detail': str(e), 'process_active': bot_process_active}
    else:
        checks['bot'] = {'status': 'offline', 'process_active': bot_process_active}
 
    # Flask process resource check
    flask_process_stats = agent_health.monitor.state.get("flask_process", {})
    if flask_process_stats:
        mem_p = flask_process_stats.get("memory_percent", 0)
        checks['flask_process'] = {
            'status': 'ok' if mem_p < 85 else 'warning',
            'cpu_percent': flask_process_stats.get("cpu_percent", 0),
            'memory_percent': mem_p,
            'memory_rss_gb': flask_process_stats.get("memory_rss_gb", 0),
            'pid': flask_process_stats.get("pid")
        }
    else:
        checks['flask_process'] = {'status': 'unknown', 'detail': 'sem telemetria recente'}

    overall = 'healthy' if all(c.get('status') in ['ok', 'warning'] for c in checks.values() if isinstance(c, dict)) else 'degraded'
    # Se algum status for degraded/error, vira degraded global. warning não degrada se não for crítico.
    if any(c.get('status') in ['error', 'missing', 'process_dead'] for c in checks.values() if isinstance(c, dict)):
        overall = 'degraded'

    return jsonify({'status': overall, 'checks': checks})


@app.route('/api/metrics-history')
def api_metrics_history():
    """
    Retorna o histórico recente persistido de CPU e RAM coletados em intervalos regulares.
    Retorna:
        Lista JSON de snapshots com timestamps de CPU e RAM.
    """
    return jsonify(list(_metrics_history))


@app.route('/api/rinha/generate_opponents', methods=['POST'])
def api_rinha_generate_opponents():
    """
    Usa o gemma4 (Ollama) para analisar o grafo desafiante atual (P1)
    e gerar uma estratégia de 100 oponentes, incluindo 5 oponentes de elite
    projetados pelo LLM e parâmetros evolutivos para os outros 95.
    """
    try:
        data = request.json or {}
        p1_stats = data.get("p1_stats", {})
        p1_nodes_count = p1_stats.get("nodes", 100)
        p1_edges_count = p1_stats.get("edges", 200)
        
        # System Prompt para o Gemma4
        sys_prompt = (
            "Você é um cientista de dados e especialista em Teoria dos Grafos da AI Factory. "
            "Seu objetivo é projetar 100 grafos competidores para enfrentar o grafo atual (P1) em um torneio. "
            "Para isso, você deve analisar o grafo P1 e criar regras matemáticas de geração de grafos e topologias avançadas. "
            "Você DEVE responder estritamente com um objeto JSON válido, sem tags markdown extras ou conversas. "
            "O JSON deve conter exatamente as seguintes chaves:\n"
            "1. 'analysis': Breve diagnóstico sobre como vencer o P1.\n"
            "2. 'elite_opponents': Uma lista de 5 objetos de grafos. Cada objeto representa um oponente customizado projetado por você contendo:\n"
            "   - 'name': Nome único e intimidador do oponente (ex: 'Hydra Core', 'Matrix Overlord').\n"
            "   - 'type': Descrição da topologia (ex: 'Hub-Spoke-Hyper-Cluster').\n"
            "   - 'nodes': Lista de objetos de nós, contendo 'id' (string) e 'label' (string). Máximo de 15 nós por oponente de elite para poupar processamento.\n"
            "   - 'edges': Lista de objetos de arestas, contendo 'source' (string) e 'target' (string).\n"
            "3. 'mutation_factors': Um objeto contendo parâmetros numéricos recomendados por você para gerar os outros 95 oponentes no frontend:\n"
            "   - 'average_node_count': Número médio de nós (ex: 50).\n"
            "   - 'hub_probability': Probabilidade de criar um nó mestre (ex: 0.15).\n"
            "   - 'rewire_probability': Probabilidade de reconectar arestas órfãs (ex: 0.25).\n"
            "   - 'clustering_factor': Coeficiente de agrupamento desejado (ex: 0.8).\n"
            "   - 'names_pool': Uma lista com 15 nomes/palavras-chave intimidadores de rede para usarmos como nomes de nós."
        )
        
        prompt = (
            f"O grafo desafiante atual P1 possui {p1_nodes_count} nós e {p1_edges_count} arestas. "
            "Desenhe a estratégia de otimização de rede e retorne o JSON estruturado."
        )
        
        # Faz chamada ao Gemma4 via local_ollama_call
        res = agent_core.local_ollama_call(prompt, sys_prompt)
        
        if not res:
            # Fallback seguro caso o Ollama falhe ou esteja desligado
            res = {
                "analysis": "Não foi possível conectar ao Gemma4. Usando o algoritmo de fallback da rinha.",
                "elite_opponents": [],
                "mutation_factors": {
                    "average_node_count": 40,
                    "hub_probability": 0.1,
                    "rewire_probability": 0.2,
                    "clustering_factor": 0.5,
                    "names_pool": ["Quantum", "Helix", "Stellar", "Core", "Node", "Nova", "Cosmos", "Apex"]
                }
            }
            
        return jsonify(res)
    except Exception as e:
        logger.error(f"Erro na geração de oponentes com Gemma4: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    # Log da exceção não tratada
    logger.error(f"Exceção não tratada na requisição HTTP: {e}", exc_info=True)
    response = {
        "error": "Internal Server Error",
        "msg": "Ocorreu um erro interno inesperado no servidor."
    }
    if app.debug:
        response["detail"] = str(e)
    return jsonify(response), 500


if __name__ == '__main__':
    flask_debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    flask_port = int(os.environ.get("PORT", 8091))
    app.run(debug=flask_debug, port=flask_port)
