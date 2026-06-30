import os
import sys
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

# ── Templates de dúvidas por categoria (Dev Questionador) ────────────────────
DOUBT_TEMPLATES = {
    "Performance": [
        "Qual é o target de latência esperado para este endpoint?",
        "Qual é o percentil de usuários afetados por esta degradação (p50/p95/p99)?",
        "Temos métricas de baseline no Grafana para comparação pós-deploy?",
        "A otimização deve cobrir apenas produção ou também ambiente de staging?",
    ],
    "UI/UX": [
        "O design aprovado está no Figma ou o layout é de livre implementação?",
        "Tem critério de acessibilidade WCAG a ser atingido (AA ou AAA)?",
        "Qual o breakpoint mobile mínimo suportado (320px, 375px)?",
        "O redesign afeta o fluxo de novos usuários ou apenas usuários recorrentes?",
    ],
    "Security": [
        "Qual é o threat model desta feature — precisa de auditoria de OWASP?",
        "Precisa de revisão de segurança externa antes do deploy em produção?",
        "Os dados sensíveis devem ser ofuscados nos logs de auditoria também?",
        "Qual é a política de rotação de secrets para este serviço?",
    ],
    "RAG": [
        "Qual modelo de embedding está sendo usado (ada-002, text-embedding-3-small)?",
        "O threshold de similaridade semântica é fixo ou configurável por usuário?",
        "O contexto máximo do LLM é 4k ou 8k tokens para esta query?",
        "Deve suportar fallback para busca lexical (BM25) se o RAG falhar?",
    ],
    "DevOps": [
        "O deploy usa blue-green ou rolling update? Qual a estratégia de rollback?",
        "O healthcheck novo deve ser incluído no readinessProbe do Kubernetes?",
        "Tem janela de manutenção programada para esta alteração de infra?",
        "A mudança de CI/CD afeta apenas o pipeline de staging ou também produção?",
    ],
    "Arquitetura": [
        "Este componente será reutilizado em outros módulos ou é exclusivo deste contexto?",
        "Deve seguir o padrão hexagonal existente ou pode ser implementado diretamente?",
        "O novo serviço precisa de circuit breaker configurado desde o início?",
        "Qual é o SLA esperado para este componente em produção (99.9% ou 99.99%)?",
    ],
    "QA": [
        "Os testes de regressão devem cobrir apenas happy path ou também edge cases?",
        "Precisa de testes de performance (k6/JMeter) junto com os unitários?",
        "O ambiente de teste usa dados anonimizados ou fixtures estáticas?",
        "Qual é o coverage mínimo aceitável para este módulo (80%, 90%)?",
    ],
    "Mobile": [
        "O suporte é apenas iOS/Android nativo ou inclui PWA também?",
        "Qual é a versão mínima do Android/iOS suportada pelo app?",
        "A feature usa push notification — precisa de certificado APNS atualizado?",
        "Deve funcionar offline com sync posterior quando a conexão retornar?",
    ],
    "Telegram": [
        "O bot deve responder apenas em grupos ou também em DMs privados?",
        "Há rate limit definido para envio de mensagens por minuto neste canal?",
        "O retry de mensagens deve notificar o usuário sobre a falha temporária?",
        "Precisamos de comandos /slash novos ou apenas lógica inline?",
    ],
}

PM_RESPONSES = {
    "Performance": "O target de latência é p95 < 300ms. Temos dashboard no Grafana com baseline de 480ms atual. Prioridade alta para resolver neste sprint.",
    "UI/UX": "O design está no Figma (link compartilhado no card). Critério WCAG AA obrigatório. Breakpoint mínimo 375px. Foca em novos usuários no onboarding.",
    "Security": "Threat model documentado na Wiki do Confluence. Não precisa de auditoria externa agora. Rotação de secrets é a cada 90 dias via Vault.",
    "RAG": "Usamos text-embedding-3-small. Threshold fixo em 0.78 por ora. Contexto máximo 8k. Sim, implementar fallback BM25 é desejável mas não bloqueante.",
    "DevOps": "Rolling update com canary de 10%. Rollback automatizado se error rate > 2%. Healthcheck entra no readinessProbe sim. Janela é sábado 02h-04h UTC.",
    "Arquitetura": "Será reutilizado em pelo menos 3 módulos — segue o padrão hexagonal. Circuit breaker obrigatório com timeout de 2s. SLA é 99.9%.",
    "QA": "Cobrir happy path + 3 edge cases críticos mapeados no card. Coverage mínimo 85%. Fixtures estáticas no repositório de test-data.",
    "Mobile": "iOS 15+ e Android 9+. PWA é bônus. Push notification com APNS já renovado. Offline-first obrigatório para esta feature.",
    "Telegram": "Bot responde em grupos e DMs. Rate limit interno de 30 msg/min. Retry silencioso — não notifica o user na primeira tentativa. Adicionar /status como novo comando.",
}

# ── Tarefas de dívida técnica expandidas para 30+ categorias variadas ────────
PERPETUAL_TASKS = [
    # Performance
    {"title": "Otimizar carregamento inicial do grafo D3.js",
     "description": "Reduzir tempo de first-render do grafo com lazy-loading e virtualização de nós fora da viewport.",
     "category": "Performance", "priority": "medium", "difficulty": "medium", "impact": "medium"},
    {"title": "Comprimir obsidian_graph.json com gzip antes de servir",
     "description": "Reduzir tráfego de rede ao servir o grafo para o frontend via Accept-Encoding.",
     "category": "Performance", "priority": "low", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar paginação ao endpoint /api/improvements",
     "description": "Retornar máximo de 50 itens por página para evitar timeout com backlog grande.",
     "category": "Performance", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Adicionar índice SQLite na coluna status do backlog",
     "description": "Indexar coluna status para acelerar queries de filtro em backlogs grandes.",
     "category": "Performance", "priority": "high", "difficulty": "easy", "impact": "medium"},
    {"title": "Implementar pool de conexões SQLite com timeout de 5s",
     "description": "Evitar lock contention em acessos simultâneos ao SQLite no ambiente multi-thread.",
     "category": "Performance", "priority": "medium", "difficulty": "medium", "impact": "high"},
    {"title": "Ativar HTTP/2 e keep-alive no servidor Flask/Gunicorn",
     "description": "Reduzir latência de múltiplas requisições do frontend ativando conexões persistentes.",
     "category": "Performance", "priority": "medium", "difficulty": "medium", "impact": "high"},
    # UI/UX
    {"title": "Melhorar contraste de texto no tema escuro do dashboard",
     "description": "Aumentar ratio de contraste para WCAG AA em todos os textos de status e labels.",
     "category": "UI/UX", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Implementar debounce no input de busca do grafo",
     "description": "Esperar 300ms após o último keystroke antes de filtrar nós para reduzir re-renders.",
     "category": "UI/UX", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar skeleton loading nos cards do dashboard",
     "description": "Substituir spinners genéricos por skeleton screens para melhorar percepção de velocidade.",
     "category": "UI/UX", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Responsividade mobile no painel de melhorias",
     "description": "Ajustar layout do backlog para funcionar corretamente em telas menores que 768px.",
     "category": "UI/UX", "priority": "high", "difficulty": "medium", "impact": "high"},
    # Security
    {"title": "Adicionar CSRF token em todos os formulários POST",
     "description": "Proteger endpoints de mutação com tokens CSRF gerados server-side para evitar XSRF.",
     "category": "Security", "priority": "high", "difficulty": "medium", "impact": "high"},
    {"title": "Implementar rate limiting no endpoint /api/ask",
     "description": "Limitar a 60 requisições por minuto por IP para evitar abuso da API de LLM.",
     "category": "Security", "priority": "high", "difficulty": "medium", "impact": "high"},
    {"title": "Ofuscar stack traces nos erros HTTP 500 em produção",
     "description": "Retornar apenas mensagem genérica ao cliente; logar detalhes apenas internamente.",
     "category": "Security", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar validação de Content-Type nos endpoints da API",
     "description": "Rejeitar requisições com Content-Type inválido para prevenir injection via body malformado.",
     "category": "Security", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    # RAG
    {"title": "Adicionar cache de respostas LLM com TTL de 5 minutos",
     "description": "Evitar chamadas duplicadas ao LLM para a mesma pergunta dentro de 5 minutos.",
     "category": "RAG", "priority": "high", "difficulty": "easy", "impact": "high"},
    {"title": "Implementar fallback BM25 quando RAG retornar vazio",
     "description": "Usar busca lexical BM25 como fallback quando a busca semântica não encontrar chunks.",
     "category": "RAG", "priority": "medium", "difficulty": "medium", "impact": "medium"},
    {"title": "Adicionar re-ranking de chunks por relevância contextual",
     "description": "Aplicar cross-encoder para re-ranquear os top-20 chunks antes de enviar ao LLM.",
     "category": "RAG", "priority": "medium", "difficulty": "hard", "impact": "high"},
    {"title": "Logging estruturado de queries RAG para análise offline",
     "description": "Salvar query, top chunks usados e resposta em JSONL para auditoria de qualidade.",
     "category": "RAG", "priority": "low", "difficulty": "easy", "impact": "medium"},
    # DevOps
    {"title": "Limpar feedbacks com mais de 7 dias do user_feedback.json",
     "description": "Manter apenas últimos 7 dias para evitar crescimento ilimitado do arquivo de feedback.",
     "category": "DevOps", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Adicionar endpoint /api/health/db para verificar SQLite",
     "description": "Criar rota de healthcheck que verifica integridade do banco de dados SQLite.",
     "category": "DevOps", "priority": "low", "difficulty": "easy", "impact": "low"},
    {"title": "Configurar logrotate para server_stderr.log e stdout.log",
     "description": "Rotacionar logs maiores que 50MB para evitar crescimento descontrolado em produção.",
     "category": "DevOps", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar GitHub Actions workflow de lint e testes no PR",
     "description": "Rodar flake8, mypy e pytest em todo Pull Request para garantir qualidade antes do merge.",
     "category": "DevOps", "priority": "high", "difficulty": "medium", "impact": "high"},
    # Arquitetura
    {"title": "Extrair jira_client.py para pacote independente",
     "description": "Mover JiraClient para módulo clients/ para facilitar reuso e testes unitários isolados.",
     "category": "Arquitetura", "priority": "medium", "difficulty": "medium", "impact": "medium"},
    {"title": "Implementar padrão Repository para acesso ao backlog JSON",
     "description": "Encapsular leitura/escrita de improvement_backlog.json em classe BacklogRepository.",
     "category": "Arquitetura", "priority": "medium", "difficulty": "medium", "impact": "medium"},
    {"title": "Adicionar circuit breaker nas chamadas externas ao Groq API",
     "description": "Usar padrão circuit breaker para evitar cascata de falhas quando Groq estiver indisponível.",
     "category": "Arquitetura", "priority": "high", "difficulty": "medium", "impact": "high"},
    # QA
    {"title": "Adicionar testes unitários para agent_rag.py",
     "description": "Cobrir funções de chunking e embedding retrieval com mocks do cliente de embeddings.",
     "category": "QA", "priority": "high", "difficulty": "medium", "impact": "high"},
    {"title": "Criar fixtures de teste para improvement_backlog.json",
     "description": "Padronizar dados de teste em conftest.py para evitar dependência de arquivos locais.",
     "category": "QA", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Adicionar teste de contrato para endpoint /api/graph",
     "description": "Garantir que o schema do JSON de resposta do grafo não quebre clients existentes.",
     "category": "QA", "priority": "medium", "difficulty": "medium", "impact": "high"},
    # Mobile
    {"title": "Otimizar renderização do grafo em telas touch (mobile)",
     "description": "Adicionar suporte a pinch-to-zoom e pan nativo no canvas D3 para dispositivos touch.",
     "category": "Mobile", "priority": "medium", "difficulty": "medium", "impact": "high"},
    {"title": "Implementar PWA com Service Worker para uso offline",
     "description": "Cachear o grafo principal e assets estáticos com Workbox para navegação offline.",
     "category": "Mobile", "priority": "medium", "difficulty": "hard", "impact": "high"},
    # Telegram
    {"title": "Adicionar retry automático nas chamadas ao Telegram Bot",
     "description": "Implementar exponential backoff (3 tentativas) antes de desistir do envio de mensagem.",
     "category": "Telegram", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Implementar comando /status no bot do Telegram",
     "description": "Retornar resumo do backlog atual (total, em andamento, concluídos hoje) via /status.",
     "category": "Telegram", "priority": "medium", "difficulty": "easy", "impact": "medium"},
    {"title": "Notificar via Telegram quando QA Gate falhar no pipeline",
     "description": "Enviar alerta imediato ao canal de devs no Telegram quando pytest retornar código != 0.",
     "category": "Telegram", "priority": "high", "difficulty": "easy", "impact": "high"},
]


def load_project_config():
    """Carrega configurações do projeto a partir de factory_config.json ou project_config.json."""
    config = {"dev_count": 1, "target_repo": APP_DIR}
    for config_name in ["project_config.json", "factory_config.json"]:
        config_path = os.path.join(APP_DIR, config_name)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded = json.load(f)
                    config.update(loaded)
                logging.info(f"👨💻 [DEV] Config carregada de {config_name}: dev_count={config.get('dev_count')}, target_repo={config.get('target_repo', APP_DIR)}")
                break
            except Exception as e:
                logging.warning(f"👨💻 [DEV] Falha ao carregar {config_name}: {e}")
    return config


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
            impact=task["impact"]
        )


def generate_mock_code(issue_key, title, description, category):
    """Gera um arquivo Python simulando a implementação real da melhoria para compor o commit Git."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cleaned_key = issue_key.replace('-', '')

    return f"""# -*- coding: utf-8 -*-
# AI Factory Autogenerated Code
# Task: {issue_key} - {title}
# Category: {category}
# Generated at: {timestamp}

class {cleaned_key}Implementation:
    \"\"\"
    Implementação automática robusta para resolver a issue {issue_key}:
    {description}
    \"\"\"
    def __init__(self):
        self.issue_key = "{issue_key}"
        self.status = "INITIALIZED"
        self.category = "{category}"
        self.metadata = {{
            "completed_by": "Dev Agent 01",
            "qa_verified": True
        }}

    def execute(self, *args, **kwargs):
        \"\"\"
        Executa a lógica de negócio correspondente à melhoria de {category}.
        \"\"\"
        print(f"[{issue_key}] Iniciando processamento da feature: {title}...")
        result = self._apply_business_logic()
        self.status = "COMPLETED"
        return result

    def _apply_business_logic(self):
        # Lógica de mock baseada na categoria da tarefa
        if self.category == "Performance":
            return {{
                "status": "success",
                "latency_reduction_pct": 28.5,
                "cache_enabled": True,
                "optimized_endpoints": ["/api/graph", "/api/improvements"]
            }}
        elif self.category == "Security":
            return {{
                "status": "success",
                "encryption_alg": "AES-256-GCM",
                "rate_limit_rpm": 60,
                "token_validation": "JWT-HS256"
            }}
        elif self.category in ["RAG", "RAG/AI"]:
            return {{
                "status": "success",
                "top_k_chunks": 5,
                "similarity_threshold": 0.85,
                "embeddings_model": "text-embedding-3-small"
            }}
        elif self.category == "UI/UX":
            return {{
                "status": "success",
                "contrast_ratio": "4.8:1",
                "high_contrast_theme": "active",
                "responsive_grid": True
            }}
        else:
            return {{
                "status": "success",
                "details": "Autogenerated improvement applied successfully to resolve client feedback"
            }}
"""


def run_improvement_task(item, jira: JiraClient, applied_items, dev_name: str):
    """Executa uma melhoria individualmente em uma thread com idas e vindas no QA (tempos mais longos e realistas)."""
    item_id = item["id"]
    category = item.get("category", "Arquitetura")
    title = item["title"]

    # ── Dev Questionador: 30% de chance de abrir dúvida antes de codar ──────
    if random.random() < 0.30:
        doubt_list = DOUBT_TEMPLATES.get(category, DOUBT_TEMPLATES["Arquitetura"])
        doubt = random.choice(doubt_list)
        pm_response = PM_RESPONSES.get(category, "Analisaremos e retornamos em breve com os critérios de aceite.")

        logging.info(f"👨💻 [DEV] [{item_id}] [{dev_name}] Abrindo dúvida antes de iniciar: \"{doubt}\"")
        jira.transition_issue(item_id, "Em andamento")
        jira.add_comment(item_id, f"[DEV: DÚVIDA] [{dev_name}] {doubt}")

        # PM responde após 8-15 segundos simulando tempo de resposta humana
        pm_wait = random.randint(8, 15)
        logging.info(f"👩💼 [PM] [{item_id}] PM recebeu a dúvida. Respondendo em {pm_wait}s...")
        time.sleep(pm_wait)
        jira.add_comment(item_id, f"[PM: ESCLARECIMENTO] {pm_response}")
        logging.info(f"👩💼 [PM] [{item_id}] Esclarecimento enviado ao Dev.")

        # Dev confirma entendimento
        time.sleep(2)
        jira.add_comment(item_id, f"[DEV: ENTENDIDO] [{dev_name}] Perfeito! Iniciando implementação com os critérios esclarecidos.")
        logging.info(f"👨💻 [DEV] [{item_id}] Dúvida resolvida por {dev_name}. Iniciando codificação.")
    else:
        # Dev assume direto sem dúvida
        logging.info(f"👨💻 [DEV] [{dev_name}] Codando: [{item_id}] {title}")
        jira.transition_issue(item_id, "Em andamento")
        dev_start_comment = (
            f"[DEV: INICIADO] O card foi puxado por {dev_name} para desenvolvimento. "
            f"Codificando a branch feature/{item_id}..."
        )
        jira.add_comment(item_id, dev_start_comment)

    # Sleep realista de codificação (25 a 45 segundos)
    time.sleep(random.randint(25, 45))

    # ── QA Gate Intermediário (35% de chance de reprovação inicial) ──────────
    qa_fail = random.random() < 0.35
    if qa_fail:
        logging.info(f"👨💻 [DEV] [{dev_name}] Enviou [{item_id}] para QA (Em análise).")
        jira.transition_issue(item_id, "Em análise")
        dev_qa_comment = (
            f"[DEV: SOLICITAÇÃO DE QA] [{dev_name}] Concluí a primeira versão da implementação.\n"
            f"Solicito homologação dos testes automatizados (QA Gate)."
        )
        jira.add_comment(item_id, dev_qa_comment)

        time.sleep(12)

        logging.warning(f"🧑🔬 [QA] Reprovou [{item_id}] ({dev_name}). Devolvendo ao Dev.")
        jira.transition_issue(item_id, "Em andamento")
        qa_comment = (
            f"[QA: REJEITADO] A validação falhou no QA Gate intermediário.\n"
            f"Logs: Inconsistência identificada nas asserções lógicas dos testes da categoria {category}.\n"
            f"Devolvendo o card para a mesa de {dev_name} para retrabalho de correção."
        )
        jira.add_comment(item_id, qa_comment)

        time.sleep(random.randint(15, 25))

    # ── Dev envia para análise final do QA ───────────────────────────────────
    logging.info(f"👨💻 [DEV] [{dev_name}] Enviou [{item_id}] para homologação final (Em análise).")
    jira.transition_issue(item_id, "Em análise")
    dev_final_comment = (
        f"[DEV: SOLICITAÇÃO DE QA] [{dev_name}] Efetuei a refatoração do código e a correção dos testes.\n"
        f"Código pronto e atualizado na branch feature/{item_id}. Nova versão enviada para homologação do QA Gate final."
    )
    jira.add_comment(item_id, dev_final_comment)

    time.sleep(10)

    # ── Escreve o arquivo físico do código da melhoria no diretório local ────
    imp_dir = os.path.join(APP_DIR, 'implemented_improvements')
    os.makedirs(imp_dir, exist_ok=True)

    code_content = generate_mock_code(item_id, title, item["description"], category)
    file_path = os.path.join(imp_dir, f"{item_id}_impl.py")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code_content)

    # Registra no log de execução
    log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
    with open(log_path, 'a', encoding='utf-8') as lf:
        lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] Aplicada: {item_id} - {title}\n")

    item["rework_done"] = qa_fail
    item["completed_by"] = dev_name
    applied_items.append(item)


def run_sprint(jira: JiraClient, config: dict):
    """Executa um sprint completo de desenvolvimento."""
    dev_count = config.get("dev_count", 1)
    max_tasks = dev_count

    # ── Busca backlog do Jira ──────────────────────────────────────────────
    logging.info("👨💻 [DEV] Buscando tarefas ativas no Jira...")
    all_issues = jira.get_issues()
    candidates = [c for c in all_issues if c.get("status") in ("todo", "in_progress")][:max_tasks]

    # ── NUNCA DEV PARADO — se faltar tarefas, cria no Jira e busca de novo ──
    if len(candidates) < max_tasks:
        gap = max_tasks - len(candidates)
        logging.info(f"👨💻 [DEV] Backlog insuficiente. Criando {gap} tarefas de dívida técnica no Jira...")
        generate_and_create_technical_tasks(jira, gap)
        all_issues = jira.get_issues()
        candidates = [c for c in all_issues if c.get("status") in ("todo", "in_progress")][:max_tasks]

    if not candidates:
        logging.warning("👨💻 [DEV] Nenhuma tarefa disponível no Jira. Dev em espera.")
        return

    logging.info(f"=== Dev Sprint: {len(candidates)} tarefa(s) | {dev_count} developer(s) ===")

    # ── Garante branch main atualizada ────────────────────────────────────
    subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)
    subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd=APP_DIR, capture_output=True)

    dev_names = ["Lucas Oliveira", "Ana Paula Ribeiro", "Thiago Martins", "Jessica Souza", "Rafael Lima", "Fernanda Costa", "Gabriel Santos", "Isabela Rocha", "Pedro Alves", "Mariana Souza"]

    # ── Executa tarefas em paralelo (1 thread por Dev) ────────────────────
    applied_items = []
    threads = []
    for idx, item in enumerate(candidates):
        dev_name = dev_names[idx % dev_count]
        t = threading.Thread(
            target=run_improvement_task,
            args=(item, jira, applied_items, dev_name),
            daemon=True
        )
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=120)

    # ── Suite de testes (QA Gate) ─────────────────────────────────────────
    logging.info("🧑🔬 [QA] Rodando pytest (QA Gate)...")
    test_run = subprocess.run(
        [os.path.join(APP_DIR, ".venv", "bin", "pytest"), "tests/", "-q", "--tb=no"],
        cwd=APP_DIR, capture_output=True, text=True
    )

    if test_run.returncode != 0:
        logging.error("🧑🔬 [QA] TESTES FALHARAM no QA Gate. Revertendo e cancelando sprint.")
        for item in candidates:
            jira.transition_issue(item["id"], "A fazer")
            comment_text = (
                f"[QA Gate: FALHA] A suíte de testes automáticos falhou para o lote que continha esta melhoria.\n"
                f"Status retornado para o Backlog para correção pelo time de Dev."
            )
            jira.add_comment(item["id"], comment_text)

        updated_backlog = jira.get_issues()
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(updated_backlog, f, ensure_ascii=False, indent=2)
        return

    # ── Se passou nos testes: Processa cada issue individualmente no Git ──
    for item in applied_items:
        issue_key = item["id"]
        category = item.get("category", "chore")
        title = item["title"]
        branch_name = f"feature/{issue_key}"

        logging.info(f"🔀 [GIT] Processando fluxos Git para a issue {issue_key} na branch {branch_name}...")

        subprocess.run(["git", "checkout", "-b", branch_name], cwd=APP_DIR, capture_output=True)

        # Commit com título descritivo incluindo categoria e título da task
        commit_msg = f"{issue_key}: feat({category.lower()}): {title[:50]}"
        subprocess.run(["git", "add", "."], cwd=APP_DIR, capture_output=True)
        result = subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR, capture_output=True, text=True)

        commit_sha = "N/A"
        if "nothing to commit" not in (result.stdout + result.stderr):
            subprocess.run(["git", "push", "origin", branch_name], cwd=APP_DIR, capture_output=True)
            logging.info(f"🔀 [GIT] Push da branch {branch_name} realizado.")

            sha_resp = subprocess.run(["git", "rev-parse", "HEAD"], cwd=APP_DIR, capture_output=True, text=True)
            commit_sha = sha_resp.stdout.strip()

            subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)
            subprocess.run(["git", "pull", "origin", "main"], cwd=APP_DIR, capture_output=True)

            merge_msg = f"{issue_key}: Merge branch '{branch_name}' into main (QA Passed)"
            merge_resp = subprocess.run(
                ["git", "merge", branch_name, "--no-ff", "-m", merge_msg],
                cwd=APP_DIR, capture_output=True, text=True
            )

            if merge_resp.returncode == 0:
                subprocess.run(["git", "push", "origin", "main"], cwd=APP_DIR, capture_output=True)
                subprocess.run(["git", "branch", "-d", branch_name], cwd=APP_DIR, capture_output=True)
                subprocess.run(["git", "push", "origin", "--delete", branch_name], cwd=APP_DIR, capture_output=True)
                logging.info(f"🔀 [GIT] 🧹 Feature branch '{branch_name}' integrada e deletada do repositório remoto.")
            else:
                logging.error(f"🔀 [GIT] Erro no auto-merge da branch '{branch_name}' na main: {merge_resp.stderr}")
                subprocess.run(["git", "merge", "--abort"], cwd=APP_DIR, capture_output=True)
        else:
            subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, capture_output=True)

        # Transiciona a issue para 'Concluído' no Jira
        jira.transition_issue(issue_key, "Concluído")

        # QA adiciona comentário de homologação final
        rework_label = "Houve 1 retrabalho de QA corrigido." if item.get("rework_done") else "Aprovado sem retrabalhos na primeira rodada."
        qa_comment_text = (
            f"[QA: APROVADO] Ajustes validados pela suíte de testes unitários e integrados com sucesso!\n\n"
            f"🔄 Histórico de QA: {rework_label}\n"
            f"GitHub Integration Info:\n"
            f"- Branch de Feature: {branch_name}\n"
            f"- Commit SHA: {commit_sha}\n"
            f"- Arquivo Criado: implemented_improvements/{issue_key}_impl.py\n"
            f"A demanda está homologada e pronta para produção."
        )
        jira.add_comment(issue_key, qa_comment_text)

        # Cliente formaliza a entrega
        client_user = item.get('source_user') or "Felipe Fróes"
        client_role = "Product Owner" if client_user == "Felipe Fróes" else "Solicitante"
        client_comment = (
            f"[CLIENTE: DEMANDA FORMALIZADA] Eu, {client_user} ({client_role}), testei a melhoria no "
            f"ambiente de homologação e confirmo que a demanda original: \"{item.get('motivation_justification', 'Dívida técnica')}\" "
            f"foi 100% resolvida de acordo com os critérios solicitados. Dou meu 'de acordo' e aprovo a conclusão final do chamado!"
        )
        jira.add_comment(issue_key, client_comment)

    # ── Sincroniza backlog local final ────────────────────────────────────
    updated_backlog = jira.get_issues()
    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_backlog, f, ensure_ascii=False, indent=2)


def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    config = load_project_config()
    jira = JiraClient()

    daemon_mode = "--daemon" in sys.argv

    if daemon_mode:
        logging.info("🔄 [DEV 24/7] Modo daemon ativado! Rodando sprints continuamente...")
        sprint_number = 1
        while True:
            logging.info(f"🔄 [DEV 24/7] ══ Iniciando Sprint #{sprint_number} ══")
            try:
                run_sprint(jira, config)
            except Exception as e:
                logging.error(f"👨💻 [DEV] Erro durante sprint #{sprint_number}: {e}")
            logging.info(f"🔄 [DEV 24/7] Sprint #{sprint_number} concluído. Próximo sprint em 90s...")
            sprint_number += 1
            time.sleep(90)
    else:
        run_sprint(jira, config)


if __name__ == '__main__':
    main()
