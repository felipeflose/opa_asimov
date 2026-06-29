"""
PM Agent — Triagem em Batch de Alta Velocidade.

Modelo: ao invés de 1 chamada LLM por reclamação (O(N) lento),
agrupa TODOS os pendentes em 1 única chamada que retorna SIM/NAO para cada um.
Aceitos → converte em card com 1 segunda chamada batch.
Resultado: 30 reclamações triadas em ~2 chamadas LLM, não em 30+.
"""
import os
import json
import re
import hashlib
import logging
import requests
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

    raw = ""
    if groq_key:
        raw = llm_post(groq_key, "gemma2-9b-it",
                       [{"role": "user", "content": prompt}], json_mode=True, max_tokens=500)
    if not raw:
        raw = llm_ollama(prompt, json_mode=True)

    try:
        data = json.loads(raw)
        results = data.get("results", [])
        if len(results) == len(complaints):
            return [bool(r) for r in results]
    except Exception:
        pass

    # Fallback heurístico: palavra-chave matching
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
    """
    if not complaints:
        return []

    numbered = "\n".join(f"{i+1}. {c}" for i, c in enumerate(complaints))
    prompt = f"""Converta cada reclamação abaixo em um card de backlog técnico.

{numbered}

Retorne APENAS um JSON no formato:
{{"cards": [
  {{"title": "Título curto", "description": "Descrição técnica", "category": "Performance|RAG|UI/UX|Security|DevOps|Arquitetura", "priority": "high|medium|low", "difficulty": "easy|medium|hard", "impact": "high|medium|low"}},
  ...
]}}

A lista deve ter exatamente {len(complaints)} cards."""

    raw = ""
    if groq_key:
        raw = llm_post(groq_key, "gemma2-9b-it",
                       [{"role": "user", "content": prompt}], json_mode=True, max_tokens=3000)
    if not raw:
        raw = llm_ollama(prompt, json_mode=True)

    try:
        data = json.loads(raw)
        cards = data.get("cards", [])
        if len(cards) == len(complaints):
            return cards
    except Exception:
        pass

    # Fallback: cria cards genéricos
    logging.warning("Conversão LLM falhou — criando cards genéricos.")
    return [{"title": c[:60], "description": c, "category": "Arquitetura",
             "priority": "medium", "difficulty": "medium", "impact": "medium"}
            for c in complaints]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    from dotenv import load_dotenv
    import threading
    load_dotenv(os.path.join(APP_DIR, '.env'))
    groq_key = os.environ.get("GROQ_API_KEY", "")

    # ── Carrega configuração de PMs ───────────────────────────
    pm_count = 1
    config_path = os.path.join(APP_DIR, 'factory_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                pm_count = json.load(f).get("pm_count", 1)
        except Exception:
            pass

    # ── Carrega backlog e feedbacks ───────────────────────────
    backlog = []
    if os.path.exists(IMPROVEMENTS_FILE):
        try:
            with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
                backlog = json.load(f)
        except Exception:
            pass

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
        return

    # ── Pre-filtragem por fingerprint (sem LLM) ───────────────
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
        _save(feedbacks, backlog, [])
        return

    # ── Divide em chunks por PM ───────────────────────────────
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

        with counter_lock:
            start = id_counter[0]
            id_counter[0] += len(cards)

        local_tasks = []
        for pos, (orig_idx, card) in enumerate(zip(truly_new, cards)):
            fb = pending[orig_idx]
            fp = complaints_fps[orig_idx]
            task_id = f"IMP-{(start + pos):05d}"
            task = {
                "id": task_id,
                "title": f"{task_id}: {card.get('title', fb['complaint'][:60])}",
                "description": card.get("description", fb["complaint"]),
                "details": f"Gerado via feedback de {fb.get('user','?')} ({fb.get('role','?')})",
                "motivation_justification": fb["complaint"],
                "category": card.get("category", "Arquitetura"),
                "status": "todo",
                "priority": card.get("priority", "high"),
                "difficulty": card.get("difficulty", "medium"),
                "impact": card.get("impact", "medium"),
                "qualified": True,
                "fingerprint": fp,
                "source_user": fb.get("user", ""),
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
            }
            local_tasks.append(task)
            fb["status"] = "accepted"
            logging.info(f"  [PM-{pm_num}] ACEITO {task_id}: {card.get('title','')[:50]}")

        with write_lock:
            all_new_tasks.extend(local_tasks)

    # ── Lança threads de PMs em paralelo ──────────────────────
    threads = []
    for pm_i, chunk in enumerate(chunks):
        t = threading.Thread(target=pm_worker, args=(chunk, pm_i + 1), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join(timeout=90)

    # ── Salva resultados ──────────────────────────────────────
    _save(feedbacks, backlog, all_new_tasks)
    todo_count = sum(1 for t in backlog if t["status"] == "todo") + len(all_new_tasks)
    logging.info(f"✅ PM({pm_count}x) concluiu: +{len(all_new_tasks)} cards. TODO: {todo_count}")


def _save(feedbacks: list, backlog: list, new_tasks: list):
    final_backlog = (
        [t for t in backlog if t["status"] != "todo"] +
        [t for t in backlog if t["status"] == "todo"] +
        new_tasks
    )
    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_backlog, f, ensure_ascii=False, indent=2)
    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(feedbacks, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()

