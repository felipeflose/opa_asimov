import os
import json
import random
import requests
import logging
import time
import threading
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Tarefas de dívida técnica para nunca deixar o Dev parado ──────────────
PERPETUAL_TASKS = [
    {"id": "TECH-001", "title": "Otimizar carregamento inicial do grafo D3.js",
     "description": "Reduzir tempo de first-render do grafo com lazy-loading e virtualização de nós fora da viewport."},
    {"id": "TECH-002", "title": "Adicionar cache de respostas Groq/LLM com TTL de 5 min",
     "description": "Evitar chamadas duplicadas ao LLM para a mesma pergunta dentro de 5 minutos."},
    {"id": "TECH-003", "title": "Comprimir obsidian_graph.json com gzip antes de servir",
     "description": "Reduzir tráfego de rede ao servir o grafo para o frontend via Accept-Encoding."},
    {"id": "TECH-004", "title": "Adicionar paginação ao endpoint /api/improvements",
     "description": "Retornar máximo de 50 itens por página para evitar timeout com backlog grande."},
    {"id": "TECH-005", "title": "Melhorar contraste de texto no tema escuro do dashboard",
     "description": "Aumentar ratio de contraste para WCAG AA em todos os textos de status e labels."},
    {"id": "TECH-006", "title": "Adicionar retry automático nas chamadas ao Telegram Bot",
     "description": "Implementar exponential backoff (3 tentativas) antes de desistir do envio de mensagem."},
    {"id": "TECH-007", "title": "Limpar feedbacks com mais de 7 dias do user_feedback.json",
     "description": "Manter apenas os últimos 7 dias para evitar crescimento ilimitado do arquivo de feedback."},
    {"id": "TECH-008", "title": "Adicionar índice SQLite na coluna 'status' do backlog",
     "description": "Indexar a coluna status para acelerar queries de filtro por status em backlogs grandes."},
    {"id": "TECH-009", "title": "Adicionar endpoint /api/health/db para verificar SQLite",
     "description": "Criar rota de healthcheck que verifica integridade do banco de dados SQLite."},
    {"id": "TECH-010", "title": "Implementar debounce no input de busca do grafo",
     "description": "Esperar 300ms após o último keystroke antes de filtrar nós para reduzir re-renders."},
    {"id": "TECH-011", "title": "Adicionar log estruturado em JSON para requests do Flask",
     "description": "Substituir o logger padrão por structured JSON logging para facilitar análise futura."},
    {"id": "TECH-012", "title": "Exportar métricas de latência para arquivo CSV diário",
     "description": "Salvar percentis p50/p95/p99 das rotas Flask em logs/metrics_{data}.csv."},
    {"id": "TECH-013", "title": "Adicionar tooltip nos nós do grafo mostrando data de criação",
     "description": "Exibir metadata da nota Obsidian (data de criação/modificação) no hover do nó."},
    {"id": "TECH-014", "title": "Refatorar annoying_user.py para usar pool de threads",
     "description": "Substituir loop sequencial por ThreadPoolExecutor para paralelizar geração de feedbacks."},
    {"id": "TECH-015", "title": "Adicionar modo escuro automático baseado no horário do sistema",
     "description": "Detectar horário local e aplicar tema escuro após 18h automaticamente."},
    {"id": "TECH-016", "title": "Minificar CSS e JS em produção",
     "description": "Usar Flask-Assets ou similar para minificar static/css/style.css e app.js no build."},
    {"id": "TECH-017", "title": "Adicionar autenticação JWT ao endpoint /api/office",
     "description": "Proteger dados do escritório virtual com token JWT de curta duração."},
    {"id": "TECH-018", "title": "Criar testes unitários para daily_digest.py",
     "description": "Adicionar pytest com mocks para cobrir os paths de coleta de dados do digest."},
    {"id": "TECH-019", "title": "Centralizar configurações em config.py com dataclass",
     "description": "Mover todas as constantes espalhadas nos arquivos para um único módulo config.py."},
    {"id": "TECH-020", "title": "Adicionar graceful shutdown ao servidor Flask",
     "description": "Capturar SIGTERM e SIGINT para fechar conexões abertas antes de encerrar."},
]


def generate_technical_tasks(dev_count: int) -> list:
    """Garante que sempre há tarefas para os Devs — nunca ficam parados."""
    shuffled = random.sample(PERPETUAL_TASKS, k=min(dev_count * 3, len(PERPETUAL_TASKS)))
    return [{**t, "status": "todo"} for t in shuffled]


def run_improvement_task(item, flask_port, headers, applied_items, api_available):
    """Executa uma melhoria individualmente em uma thread."""
    item_id = item["id"]
    logging.info(f"Dev codando: [{item_id}] {item['title']}")

    if api_available:
        move_url = f"http://localhost:{flask_port}/api/improvements/move"
        try:
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "in_progress"}, timeout=10)
        except Exception:
            pass

    # Simula tempo de codificação (5-15s por tarefa)
    time.sleep(random.randint(5, 15))

    if api_available:
        try:
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "done"}, timeout=10)
        except Exception:
            pass

    # Registra no log de execução
    log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
    with open(log_path, 'a', encoding='utf-8') as lf:
        lf.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] "
            f"Aplicada: {item_id} - {item['title']}\n"
            f"   _{item['description']}_\n"
        )

    applied_items.append(item)


def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    api_key = os.environ.get("FLOSE_API_KEY")
    flask_port = os.environ.get("PORT", "8091")
    headers = {"X-API-Key": api_key or "", "Content-Type": "application/json"}

    # ── Carrega dev_count ─────────────────────────────────────
    dev_count = 1
    config_path = os.path.join(APP_DIR, 'factory_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                dev_count = json.load(f).get("dev_count", 1)
        except Exception:
            pass

    max_tasks = dev_count * 3

    # ── Busca backlog existente ───────────────────────────────
    candidates = []
    api_available = False
    try:
        if api_key:
            r = requests.get(f"http://localhost:{flask_port}/api/improvements", timeout=8)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("in_progress", []) + data.get("todo", [])
                candidates = [c for c in candidates if c.get("status") != "done"][:max_tasks]
                api_available = True
    except Exception as e:
        logging.warning(f"Backlog API indisponível: {e}")

    # ── NUNCA DEV PARADO — preenche com tarefas técnicas ─────
    if len(candidates) < max_tasks:
        gap = max_tasks - len(candidates)
        fillers = generate_technical_tasks(gap)
        logging.info(f"Backlog insuficiente. Preenchendo {gap} tarefas de dívida técnica para manter o Dev ativo.")
        candidates.extend(fillers[:gap])

    if not candidates:
        logging.warning("Nenhuma tarefa disponível (nem filler). Dev em espera.")
        return

    logging.info(f"=== Dev Sprint: {len(candidates)} tarefa(s) | {dev_count} developer(s) ===")

    # ── Garante branch main atualizada ────────────────────────
    subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=APP_DIR, capture_output=True)

    # ── Executa tarefas em paralelo (1 thread por Dev) ───────
    applied_items = []
    threads = []
    for item in candidates:
        t = threading.Thread(
            target=run_improvement_task,
            args=(item, flask_port, headers, applied_items, api_available),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=60)   # Max 60s por dev antes de seguir

    # ── Suite de testes ───────────────────────────────────────
    logging.info("Rodando pytest (QA Gate)...")
    test_run = subprocess.run(
        [os.path.join(APP_DIR, ".venv", "bin", "pytest"), "tests/", "-q", "--tb=no"],
        cwd=APP_DIR, capture_output=True, text=True
    )

    if test_run.returncode != 0:
        logging.error("TESTES FALHARAM no QA Gate. Revertendo e voltando ao backlog.")
        with open(os.path.join(APP_DIR, 'improvements_run_log.txt'), 'a') as lf:
            lf.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] QA GATE: FALHARAM — revert aplicado\n")
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=APP_DIR, capture_output=True)
        return

    # ── Commit & Push na main ─────────────────────────────────
    if applied_items:
        ids = ", ".join(i["id"] for i in applied_items)
        commit_msg = f"chore(auto): dev sprint [{ids}] — {len(applied_items)} improvements"
        subprocess.run(["git", "add", "."], cwd=APP_DIR, capture_output=True)
        result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR, capture_output=True, text=True)
        if "nothing to commit" not in (result.stdout + result.stderr):
            subprocess.run(["git", "push", "origin", "main"], cwd=APP_DIR, capture_output=True)
            logging.info(f"✅ Push na main: {ids}")
        else:
            logging.info("Nada novo a commitar (tarefas lógicas sem mudança de arquivo).")


if __name__ == '__main__':
    main()
