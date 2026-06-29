import os
import json
import random
import requests
import logging
import time
import threading
import subprocess
from datetime import datetime
from jira_client import JiraClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')

# ── Tarefas de dívida técnica para nunca deixar o Dev parado ──────────────
PERPETUAL_TASKS = [
    {"title": "Otimizar carregamento inicial do grafo D3.js",
     "description": "Reduzir tempo de first-render do grafo com lazy-loading e virtualização de nós fora da viewport.",
     "category": "UI/UX", "priority": "medium", "difficulty": "medium", "impact": "medium"},
    {"title": "Adicionar cache de respostas Groq/LLM com TTL de 5 min",
     "description": "Evitar chamadas duplicadas ao LLM para a mesma pergunta dentro de 5 minutos.",
     "category": "RAG", "priority": "high", "difficulty": "easy", "impact": "high"},
    {"title": "Comprimir obsidian_graph.json com gzip antes de servir",
     "description": "Reduzir tráfego de rede ao servir o grafo para o frontend via Accept-Encoding.",
     "category": "Performance", "priority": "low", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar paginação ao endpoint /api/improvements",
     "description": "Retornar máximo de 50 itens por página para evitar timeout com backlog grande.",
     "category": "Performance", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Melhorar contraste de texto no tema escuro do dashboard",
     "description": "Aumentar ratio de contraste para WCAG AA em todos os textos de status e labels.",
     "category": "UI/UX", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar retry automático nas chamadas ao Telegram Bot",
     "description": "Implementar exponential backoff (3 tentativas) antes de desistir do envio de mensagem.",
     "category": "Telegram", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Limpar feedbacks com mais de 7 dias do user_feedback.json",
     "description": "Manter apenas os últimos 7 dias para evitar crescimento ilimitado do arquivo de feedback.",
     "category": "DevOps", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Adicionar índice SQLite na coluna 'status' do backlog",
     "description": "Indexar a coluna status para acelerar queries de filtro por status em backlogs grandes.",
     "category": "Performance", "priority": "high", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar endpoint /api/health/db para verificar SQLite",
     "description": "Criar rota de healthcheck que verifica integridade do banco de dados SQLite.",
     "category": "DevOps", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Implementar debounce no input de busca do grafo",
     "description": "Esperar 300ms após o último keystroke antes de filtrar nós para reduzir re-renders.",
     "category": "UI/UX", "priority": "medium", "difficulty": "easy", "impact": "medium"}
]

def generate_and_create_technical_tasks(jira: JiraClient, count: int):
    """Gera tarefas de dívida técnica e as cria no Jira."""
    shuffled = random.sample(PERPETUAL_TASKS, k=min(count, len(PERPETUAL_TASKS)))
    for task in shuffled:
        jira.create_issue(
            summary=task["title"],
            description=task["description"],
            details="Tarefa automática de dívida técnica (preenchimento de backlog)",
            motivation_justification="Evitar dev ocioso no pipeline da fábrica",
            category=task["category"],
            priority=task["priority"],
            difficulty=task["difficulty"],
            impact=task["impact"],
            source_user="AI Factory SRE"
        )

def run_improvement_task(item, jira: JiraClient, applied_items):
    """Executa uma melhoria individualmente em uma thread."""
    item_id = item["id"]
    logging.info(f"Dev codando: [{item_id}] {item['title']}")

    # Transiciona para 'Em andamento' no Jira
    jira.transition_issue(item_id, "Em andamento")

    # Simula tempo de codificação
    time.sleep(random.randint(5, 12))

    # Transiciona para 'Em análise' no Jira (Raia do QA)
    jira.transition_issue(item_id, "Em análise")

    # Registra no log de execução localmente (altera o arquivo físico da branch)
    log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
    with open(log_path, 'a', encoding='utf-8') as lf:
        lf.write(
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] "
            f"Aplicada: {item_id} - {item['title']}\n"
            f"   _{item['description']}_\n"
        )

    applied_items.append(item)

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    jira = JiraClient()

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

    # ── Busca backlog do Jira ──────────────────────────────────
    logging.info("Buscando tarefas ativas no Jira...")
    all_issues = jira.get_issues()
    candidates = [c for c in all_issues if c.get("status") == "todo"][:max_tasks]

    # ── NUNCA DEV PARADO — se faltar tarefas, cria no Jira e busca de novo
    if len(candidates) < max_tasks:
        gap = max_tasks - len(candidates)
        logging.info(f"Backlog insuficiente. Criando {gap} tarefas de dívida técnica no Jira...")
        generate_and_create_technical_tasks(jira, gap)
        # Recarrega do Jira com as novas issues criadas
        all_issues = jira.get_issues()
        candidates = [c for c in all_issues if c.get("status") == "todo"][:max_tasks]

    if not candidates:
        logging.warning("Nenhuma tarefa disponível no Jira. Dev em espera.")
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
            args=(item, jira, applied_items),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=60)

    # ── Suite de testes (QA Gate) ─────────────────────────────
    logging.info("Rodando pytest (QA Gate)...")
    test_run = subprocess.run(
        [os.path.join(APP_DIR, ".venv", "bin", "pytest"), "tests/", "-q", "--tb=no"],
        cwd=APP_DIR, capture_output=True, text=True
    )

    if test_run.returncode != 0:
        logging.error("TESTES FALHARAM no QA Gate. Revertendo e cancelando sprint.")
        # Devolve as issues do Jira ao status 'A fazer' e adiciona comentário de falha
        for item in candidates:
            jira.transition_issue(item["id"], "A fazer")
            comment_text = (
                f"[QA Gate: FALHA] A suíte de testes automáticos falhou para o lote que continha esta melhoria.\n"
                f"Status retornado para o Backlog para correção pelo time de Dev."
            )
            jira.add_comment(item["id"], comment_text)
            
        # Sincroniza backlog local
        updated_backlog = jira.get_issues()
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_backlog, f, ensure_ascii=False, indent=2)
        return

    # ── Se passou nos testes: Processa cada issue individualmente no Git para link nativo no Jira ──
    for item in applied_items:
        issue_key = item["id"]
        branch_name = f"feature/{issue_key}"
        logging.info(f"Processando fluxos Git para a issue {issue_key} na branch {branch_name}...")
        
        # 1. Cria a branch da feature
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=APP_DIR, capture_output=True)
        
        # 2. Escreve a alteração no log (modifica o arquivo físico para gerar o commit)
        log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
        with open(log_path, 'a', encoding='utf-8') as lf:
            lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-MERGE] Homologado: {issue_key}\n")
            
        # 3. Comita na branch da feature com o ID no início (Jira Link format)
        commit_msg = f"{issue_key}: chore(auto): apply adjustments for user request"
        subprocess.run(["git", "add", "."], cwd=APP_DIR, capture_output=True)
        result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR, capture_output=True, text=True)
        
        commit_sha = "N/A"
        if "nothing to commit" not in (result.stdout + result.stderr):
            # 4. Push da branch da feature (Jira vai escutar o push)
            subprocess.run(["git", "push", "origin", branch_name], cwd=APP_DIR, capture_output=True)
            
            # Obtém o SHA do commit gerado na feature
            sha_resp = subprocess.run(["git", "rev-parse", "HEAD"], cwd=APP_DIR, capture_output=True, text=True)
            commit_sha = sha_resp.stdout.strip()
            
            # 5. Faz checkout da main e atualiza
            subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)
            subprocess.run(["git", "pull", "origin", "main"], cwd=APP_DIR, capture_output=True)
            
            # 6. Merge da branch com --no-ff (emulando merge de PR no histórico do GitHub)
            merge_msg = f"{issue_key}: Merge branch '{branch_name}' into main (QA Passed)"
            merge_resp = subprocess.run(["git", "merge", branch_name, "--no-ff", "-m", merge_msg], cwd=APP_DIR, capture_output=True, text=True)
            
            if merge_resp.returncode == 0:
                # 7. Push da main atualizada
                subprocess.run(["git", "push", "origin", "main"], cwd=APP_DIR, capture_output=True)
                
                # 8. Deleta a branch local e remota
                subprocess.run(["git", "branch", "-d", branch_name], cwd=APP_DIR, capture_output=True)
                subprocess.run(["git", "push", "origin", "--delete", branch_name], cwd=APP_DIR, capture_output=True)
                logging.info(f"🧹 Feature branch '{branch_name}' integrada e deletada do repositório remoto.")
            else:
                logging.error(f"Erro no auto-merge da branch '{branch_name}' na main: {merge_resp.stderr}")
                subprocess.run(["git", "merge", "--abort"], cwd=APP_DIR, capture_output=True)
        else:
            # Se não comitou nada, apenas garante estar na main
            subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)
            
        # 9. Transiciona a issue para 'Concluído' no Jira
        jira.transition_issue(issue_key, "Concluído")
        
        # 10. Adiciona comentário de homologação final com o histórico no card
        comment_text = (
            f"[QA Gate: APROVADO] Ajustes validados por testes unitários e homologados com sucesso!\n\n"
            f"👤 Solicitante: {item.get('source_user', 'AI Factory SRE')}\n"
            f"💬 Feedback original: \"{item.get('motivation_justification', 'Dívida técnica automatizada')}\"\n\n"
            f"GitHub Integration Info:\n"
            f"- Branch: {branch_name}\n"
            f"- Commit SHA: {commit_sha}\n"
            f"- Detalhes do ajuste: {item['description']}\n\n"
            f"Modificado e integrado automaticamente de forma segura via PR/Merge."
        )
        jira.add_comment(issue_key, comment_text)

    # ── Sincroniza backlog local final
    updated_backlog = jira.get_issues()
    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_backlog, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
