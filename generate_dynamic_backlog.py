"""
PM Agent — Triagem em Batch de Alta Velocidade.

Modelo: ao invés de 1 chamada LLM por reclamação (O(N) lento),
agrupa TODOS os pendentes em 1 única chamada que retorna SIM/NAO para cada um.
Aceitos → converte em card com 1 segunda chamada batch.
Resultado: 30 reclamações triadas em ~2 chamadas LLM, não em 30+.

Modelos: Groq (gemma2-9b-it) → fallback Ollama (gemma4-fast:latest)
PM rigoroso: rejeita feedbacks sem evidências mensuráveis.
Épicos: vinculados automaticamente por categoria.
"""
import os
import json
import re
import hashlib
import logging
import requests
import random
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR        = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')
RUN_LOG_FILE   = os.path.join(APP_DIR, 'improvements_run_log.txt')
FEEDBACK_FILE  = os.path.join(APP_DIR, 'user_feedback.json')


# ── Utilitários ───────────────────────────────────────────────────────────────

def complaint_fingerprint(text: str) -> str:
    """Hash curto para deduplicação rápida sem LLM."""
    normalized = " ".join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def existing_fingerprints(backlog: list) -> set:
    return {t.get("fingerprint", "") for t in backlog if t.get("fingerprint")}


def next_id(backlog: list) -> int:
    last = 0
    for t in backlog:
        try:
            n = int(t["id"].split("-")[-1])
            last = max(last, n)
        except Exception:
            pass
    return last + 1


# ── LLM helpers ───────────────────────────────────────────────────────────────

def llm_post(groq_key: str, model: str, messages: list, json_mode=False, max_tokens=4000) -> str:
    """Chama Groq e retorna o texto da resposta, ou '' em erro."""
    try:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        logging.warning(f"Groq status {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logging.warning(f"Groq error: {e}")
    return ""


def llm_ollama(prompt: str, json_mode=False) -> str:
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "gemma4-fast:latest", "prompt": prompt, "stream": False,
                  "format": "json" if json_mode else None, "options": {"temperature": 0.1}},
            timeout=60,
        )
        if r.status_code == 200:
            return r.json()["response"].strip()
    except Exception as e:
        logging.warning(f"Ollama error: {e}")
    return ""


def llm_call(groq_key: str, messages: list, json_mode=False, max_tokens=4000) -> str:
    """Fallback chain: Groq (gemma2-9b-it) → Ollama (gemma4-fast:latest)."""
    raw = ""
    if groq_key:
        raw = llm_post(groq_key, "gemma2-9b-it", messages,
                       json_mode=json_mode, max_tokens=max_tokens)
    if not raw:
        # Monta prompt simples para Ollama (que usa generate, não chat)
        prompt = "\n".join(m["content"] for m in messages)
        raw = llm_ollama(prompt, json_mode=json_mode)
    return raw


# ── Verificação de evidências (PM rigoroso) ───────────────────────────────────

# Padrões que indicam evidência concreta no texto
_EVIDENCE_PATTERNS = [
    re.compile(r'\d+[.,]?\d*\s*(%|ms|s|seg|min|kb|mb|gb|requisições|req|nós|notas|linhas)', re.IGNORECASE),
    re.compile(r'\d+\s*(vezes|vez|usuários|requests|chamadas)', re.IGNORECASE),
    re.compile(r'(toda\s+vez|sempre\s+que|toda\s+execução|em\s+todos)', re.IGNORECASE),
    re.compile(r'/[a-zA-Z_/]+\.(py|js|json|html|sh|yml|yaml)', re.IGNORECASE),  # arquivo específico
    re.compile(r'/(api|rest|v\d)/[a-zA-Z_/]+', re.IGNORECASE),                   # endpoint específico
    re.compile(r'\b(agent_\w+|app\.py|server\.py|jira_client|vault_embeddings|obsidian_graph|user_feedback)\b', re.IGNORECASE),
    re.compile(r'(database is locked|KeyError|stack trace|HTTP \d{3}|status \d{3})', re.IGNORECASE),
    re.compile(r'\b\d{1,4}\s*(ms|segundos|minutos|horas|KB|MB|GB)\b', re.IGNORECASE),
    re.compile(r'(DevTools|Lighthouse|profiler|benchmark|medido|mensurado)', re.IGNORECASE),
    re.compile(r'\b\d+\+?\s*notas\b', re.IGNORECASE),
]


def has_evidence(complaint_text: str) -> bool:
    """
    Verifica se o texto da reclamação contém evidência concreta.
    Evidência = número/percentual, tempo, frequência, componente específico, ação reproduzível.
    """
    for pattern in _EVIDENCE_PATTERNS:
        if pattern.search(complaint_text):
            return True
    return False


def reject_feedback(fb: dict, feedbacks: list, reason: str):
    """Marca feedback como rejeitado com motivo e dica para melhoria."""
    fb["status"] = "rejected_insufficient_evidence"
    fb["rejection_reason"] = reason
    fb["rejection_tip"] = (
        "Para que sua demanda seja aceita pelo PM, inclua pelo menos um dos: "
        "número/percentual, tempo em ms/s/min, frequência (X vezes, toda vez), "
        "nome de componente específico (ex: /api/graph, agent_rag.py) ou "
        "erro reproduzível (ex: KeyError, HTTP 500)."
    )
    logging.info(f"  [PM REJEITA - SEM EVIDÊNCIA] {fb.get('user','?')}: {fb.get('complaint','')[:60]}")


# ── Mapeamento categoria → épico ──────────────────────────────────────────────

CATEGORY_TO_EPIC_AREA = {
    "Performance": "Performance",
    "Security": "Security",
    "RAG/AI": "RAG/AI",
    "RAG": "RAG/AI",
    "UI/UX": "UI/UX",
    "Frontend": "UI/UX",
    "DevOps": "DevOps",
    "Arquitetura": "Arquitetura",
    "Backend": "Arquitetura",
    "Mobile": "Mobile",
    "Telegram": "Telegram",
    "QA": "QA",
    "Data": "Arquitetura",
    "SRE": "DevOps",
    "Product": "Arquitetura",
    "Full Stack": "Arquitetura",
}


def safe_title(title: str, max_len: int = 60) -> str:
    """Trunca título de forma segura: sem cortar no meio de palavra, sem ponto final."""
    title = title.strip().rstrip(".")
    if len(title) <= max_len:
        return title
    truncated = title[:max_len].rsplit(' ', 1)[0]
    return truncated.rstrip(".,;:").strip()


# ── Triagem em Batch ──────────────────────────────────────────────────────────

def batch_triage(complaints: list[str], backlog_titles: list[str], groq_key: str) -> list[bool]:
    """
    1 chamada LLM para triage de N reclamações.
    Retorna lista de booleanos: True = duplicado/irrelevante, False = novo e válido.
    """
    if not complaints:
        return []

    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(complaints))
    backlog_ctx = "\n".join(f"- {t}" for t in backlog_titles[:60]) or "Backlog vazio."

    prompt = f"""Você é um PM de software. Analise as reclamações abaixo e decida quais já estão cobertas pelo backlog existente (DUPLICADO) e quais são novas melhorias válidas (NOVO).

BACKLOG ATUAL:
{backlog_ctx}

RECLAMAÇÕES (numeradas):
{numbered}

Responda APENAS com um JSON no formato:
{{"results": [true, false, true, ...]}}

Onde: true = DUPLICADO ou irrelevante, false = NOVO e válido.
A lista deve ter exatamente {len(complaints)} elementos booleanos."""

    raw = llm_call(groq_key, [{"role": "user", "content": prompt}], json_mode=True, max_tokens=500)

    try:
        data = json.loads(raw)
        results = data.get("results", [])
        if len(results) == len(complaints):
            return [bool(r) for r in results]
    except Exception:
        pass

    # Fallback heurístico
    logging.warning("Triage LLM falhou — usando fallback heurístico.")
    backlog_text = " ".join(backlog_titles).lower()
    out = []
    for c in complaints:
        words = [w for w in c.lower().split() if len(w) > 5]
        hits = sum(1 for w in words if w in backlog_text)
        out.append(hits >= 2)
    return out


# ── Conversão Batch ───────────────────────────────────────────────────────────

def batch_convert(complaints: list[str], groq_key: str) -> list[dict]:
    """
    1 chamada LLM para converter N reclamações em cards do backlog.
    Títulos: máximo 60 caracteres, sem ponto final, sem truncamento no meio de palavra, em português.
    """
    if not complaints:
        return []

    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(complaints))
    prompt = f"""Converta cada reclamação abaixo em um card de backlog técnico.

{numbered}

Regras para o título:
- Máximo 60 caracteres
- Sem ponto final
- Nunca corte no meio de uma palavra
- Em português
- Seja específico e técnico

Retorne APENAS um JSON no formato:
{{"cards": [
  {{"title": "Título curto e preciso em pt-BR", "description": "Descrição técnica detalhada", "category": "Performance|RAG/AI|UI/UX|Security|DevOps|Arquitetura|Mobile|QA|Telegram", "priority": "high|medium|low", "difficulty": "easy|medium|hard", "impact": "high|medium|low"}},
  ...
]}}

A lista deve ter exatamente {len(complaints)} cards."""

    raw = llm_call(groq_key, [{"role": "user", "content": prompt}], json_mode=True, max_tokens=3000)

    try:
        data = json.loads(raw)
        cards = data.get("cards", [])
        if len(cards) == len(complaints):
            # Aplica truncamento seguro em Python
            for card in cards:
                card["title"] = safe_title(card.get("title", ""), 60)
            return cards
    except Exception:
        pass

    # Fallback: cria cards genéricos
    logging.warning("Conversão LLM falhou — criando cards genéricos.")
    return [{"title": safe_title(c, 60), "description": c, "category": "Arquitetura",
             "priority": "medium", "difficulty": "medium", "impact": "medium"}
            for c in complaints]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from dotenv import load_dotenv
    import threading
    from jira_client import JiraClient
    load_dotenv(os.path.join(APP_DIR, '.env'))
    groq_key = os.environ.get("GROQ_API_KEY", "")

    # ── Inicializa JiraClient e épicos ────────────────────────────────────────
    jira = JiraClient()
    logging.info("Garantindo épicos no Jira...")
    try:
        epic_map = jira.ensure_epics()
        logging.info(f"Épicos disponíveis: {epic_map}")
    except Exception as e:
        logging.warning(f"Não foi possível garantir épicos: {e}")
        epic_map = {}

    # ── Carrega configuração de PMs ───────────────────────────────────────────
    pm_count = 1
    config_path = os.path.join(APP_DIR, 'factory_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                pm_count = json.load(f).get("pm_count", 1)
        except Exception:
            pass

    # ── Carrega backlog do Jira e feedbacks locais ────────────────────────────
    logging.info("Carregando backlog do Jira...")
    backlog = jira.get_issues()

    feedbacks = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except Exception:
            pass

    pending = [fb for fb in feedbacks if fb.get("status") == "pending"]
    logging.info(f"PM recebeu {len(pending)} feedbacks pendentes | {pm_count} PM(s) ativos.")

    if not pending:
        logging.info("Nenhum feedback pendente. PM em modo standby.")
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(backlog, f, ensure_ascii=False, indent=2)
        return

    # ── PM Rigoroso: verifica evidências antes de tudo ────────────────────────
    without_evidence = []
    pending_after_evidence = []
    for fb in pending:
        if has_evidence(fb.get("complaint", "")):
            pending_after_evidence.append(fb)
        else:
            reject_feedback(fb, feedbacks,
                            "Reclamação sem evidências mensuráveis — faltam números, "
                            "tempos, componentes específicos ou erros reproduzíveis.")
            without_evidence.append(fb)

    logging.info(f"PM rigoroso: {len(without_evidence)} rejeitados por falta de evidência | "
                 f"{len(pending_after_evidence)} seguem para triagem.")

    if not pending_after_evidence:
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(backlog, f, ensure_ascii=False, indent=2)
        return

    pending = pending_after_evidence

    # ── Pre-filtragem por fingerprint (sem LLM) ───────────────────────────────
    known_fps      = existing_fingerprints(backlog)
    backlog_titles = [f"{t['id']}: {t['title']}" for t in backlog if t.get("status") != "done"]

    complaints_text = [fb["complaint"] for fb in pending]
    complaints_fps  = [complaint_fingerprint(c) for c in complaints_text]

    to_triage_idxs = []
    for i, (fp, fb) in enumerate(zip(complaints_fps, pending)):
        if fp in known_fps:
            fb["status"] = "duplicate"
            logging.info(f"[PREFILTER] FP duplicado: {fb.get('user','?')} — '{fb['complaint'][:50]}'")
        else:
            to_triage_idxs.append(i)

    logging.info(f"Pré-filtragem: {len(to_triage_idxs)} novos para triagem LLM.")
    if not to_triage_idxs:
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(backlog, f, ensure_ascii=False, indent=2)
        return

    # ── Divide em chunks por PM ───────────────────────────────────────────────
    chunk_size = max(1, len(to_triage_idxs) // pm_count + (1 if len(to_triage_idxs) % pm_count else 0))
    chunks = [to_triage_idxs[i:i+chunk_size] for i in range(0, len(to_triage_idxs), chunk_size)]

    all_new_tasks = []
    counter_lock  = threading.Lock()
    write_lock    = threading.Lock()
    id_counter    = [next_id(backlog)]  # mutable via lista

    def pm_worker(chunk_idxs: list, pm_num: int):
        chunk_complaints = [complaints_text[i] for i in chunk_idxs]
        logging.info(f"  [PM-{pm_num}] Triando {len(chunk_complaints)} reclamações...")

        are_dups = batch_triage(chunk_complaints, backlog_titles, groq_key)

        truly_new = [chunk_idxs[j] for j, dup in enumerate(are_dups) if not dup]
        for j, dup in enumerate(are_dups):
            if dup:
                pending[chunk_idxs[j]]["status"] = "duplicate"

        if not truly_new:
            logging.info(f"  [PM-{pm_num}] Nenhum item novo após triagem.")
            return

        accepted_complaints = [complaints_text[i] for i in truly_new]
        cards = batch_convert(accepted_complaints, groq_key)

        for pos, (orig_idx, card) in enumerate(zip(truly_new, cards)):
            fb = pending[orig_idx]
            fp = complaints_fps[orig_idx]

            title = safe_title(card.get('title', fb['complaint']), 60)
            desc = card.get('description', fb['complaint'])
            details = f"Gerado via feedback de {fb.get('user','?')} ({fb.get('role','?')})"

            category = card.get("category", "Arquitetura")
            priority = card.get("priority", "high")
            difficulty = card.get("difficulty", "medium")
            impact = card.get("impact", "medium")

            # Determina épico para a categoria
            epic_area = CATEGORY_TO_EPIC_AREA.get(category, "Arquitetura")
            epic_key_val = epic_map.get(epic_area, "")

            # Cria a issue no Jira com épico vinculado
            jira_key = jira.create_issue(
                summary=title,
                description=desc,
                details=details,
                motivation_justification=fb["complaint"],
                category=category,
                priority=priority,
                difficulty=difficulty,
                impact=impact,
                source_user=fb.get("user", ""),
                fingerprint=fp,
                epic_key=epic_key_val or None,
            )

            if not jira_key:
                with counter_lock:
                    start = id_counter[0]
                    id_counter[0] += 1
                jira_key = f"IMP-{(start + pos):05d}"
            else:
                # Comentário PM enriquecido com épico e evidências
                evidences_found = [p.pattern for p in _EVIDENCE_PATTERNS if p.search(fb["complaint"])]
                epic_info = f"{epic_area} → {epic_key_val}" if epic_key_val else "sem épico"
                pm_comment = (
                    f"[PM: DEMANDA ACEITA] ✅ A demanda foi validada, classificada e está apta para desenvolvimento.\n"
                    f"Categoria: {category} | Prioridade: {priority.upper()} | Dificuldade: {difficulty} | Impacto: {impact}\n"
                    f"Épico vinculado: {epic_info}\n"
                    f"Evidências identificadas: {len(evidences_found)} padrão(ões) encontrado(s)\n"
                    f"Fonte: {fb.get('user','?')} ({fb.get('role','?')}, área: {fb.get('area','?')})"
                )
                jira.add_comment(jira_key, pm_comment)

            task = {
                "id": jira_key,
                "title": title,
                "description": desc,
                "details": details,
                "motivation_justification": fb["complaint"],
                "category": category,
                "status": "todo",
                "priority": priority,
                "difficulty": difficulty,
                "impact": impact,
                "qualified": True,
                "fingerprint": fp,
                "source_user": fb.get("user", ""),
                "epic_key": epic_key_val or "",
                "epic_area": epic_area,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }

            fb["status"] = "accepted"
            logging.info(f"  [PM-{pm_num}] ACEITO Jira {jira_key}: {title[:50]}")

            with write_lock:
                all_new_tasks.append(task)
                try:
                    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
                        json.dump(feedbacks, f, ensure_ascii=False, indent=2)
                    current_backlog = []
                    if os.path.exists(IMPROVEMENTS_FILE):
                        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
                            current_backlog = json.load(f)
                    if not any(t["id"] == jira_key for t in current_backlog):
                        current_backlog.append(task)
                    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(current_backlog, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logging.error(f"Erro na sincronização rápida do backlog pelo PM: {e}")

            time.sleep(random.randint(5, 10))

    # ── Lança threads de PMs em paralelo ─────────────────────────────────────
    threads = []
    for pm_i, chunk in enumerate(chunks):
        t = threading.Thread(target=pm_worker, args=(chunk, pm_i + 1), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=90)

    # ── Sincroniza backlog local com o Jira ───────────────────────────────────
    logging.info("Sincronizando backlog local com o Jira...")
    jira_backlog = jira.get_issues()

    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)

    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(jira_backlog, f, ensure_ascii=False, indent=2)

    todo_count = sum(1 for t in jira_backlog if t["status"] == "todo")
    logging.info(f"✅ PM({pm_count}x) concluiu. Backlog TODO atualizado do Jira: {todo_count}")


if __name__ == '__main__':
    main()
