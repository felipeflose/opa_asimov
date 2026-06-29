import os
import json
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')
RUN_LOG_FILE = os.path.join(APP_DIR, 'improvements_run_log.txt')
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')

def get_codebase_summary():
    """Analisa os arquivos do projeto para gerar um resumo do contexto atual."""
    files_to_check = [
        "app.py", "agent_rag.py", "agent_bot.py", "agent_sanitizer.py", 
        "agent_health.py", "agent_core.py", "qualify_backlog.py", "mystery_client.py"
    ]
    summary = []
    for f in files_to_check:
        path = os.path.join(APP_DIR, f)
        if os.path.exists(path):
            size = os.path.getsize(path)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                imports = [line.strip() for line in lines if line.startswith("import ") or line.startswith("from ")]
                defs = [line.strip() for line in lines if line.startswith("def ") or line.startswith("class ")]
                summary.append(f"- **{f}** ({size} bytes): Imports: {len(imports)}, Defs/Classes: {len(defs)}")
            except Exception:
                pass
    return "\n".join(summary)

def get_recent_improvements():
    """Lê as últimas melhorias aplicadas do log de execução."""
    if not os.path.exists(RUN_LOG_FILE):
        return "Nenhuma melhoria registrada ainda."
    try:
        with open(RUN_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return "".join(lines[-25:])
    except Exception:
        return "Erro ao ler histórico."

def check_is_duplicate(backlog_items, complaint):
    """Consulta o LLM para ver se a reclamação do usuário já está coberta por algum card do backlog."""
    titles = [f"- {t['id']}: {t['title']} ({t['description']})" for t in backlog_items]
    joined_titles = "\n".join(titles[:50])
    prompt = f"""Analise se a reclamação do usuário já está coberta ou resolvida por alguma das tarefas do backlog abaixo.

---
RECLAMAÇÃO: "{complaint}"
---
TAREFAS NO BACKLOG:
{joined_titles}
---

Responda apenas com a palavra "SIM" se a reclamação já estiver coberta/duplicada por alguma tarefa, ou "NAO" se for uma reclamação inédita que exige uma nova tarefa. Não explique nada, responda apenas SIM ou NAO."""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "gemma2-9b-it",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": 5
                },
                timeout=10
            )
            if r.status_code == 200:
                answer = r.json()["choices"][0]["message"]["content"].strip().upper()
                return "SIM" in answer
        except Exception:
            pass

    # Fallback Ollama Local
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4-fast:latest",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=60
        )
        if r.status_code == 200:
            answer = r.json()["response"].strip().upper()
            return "SIM" in answer
    except Exception as e:
        logging.error(f"Erro ao consultar LLM local para duplicidade: {e}")
    
    # Heurística de fallback caso offline
    for t in backlog_items:
        if any(word in t['title'].lower() or word in t['description'].lower() for word in complaint.lower().split() if len(word) > 4):
            return True
    return False

def convert_complaint_to_task(complaint):
    """Consulta o LLM para transformar a reclamação de usuário em uma tarefa técnica estruturada."""
    prompt = f"""Converta esta reclamação informal de usuário em uma tarefa de melhoria técnica de software estruturada para o backlog.

RECLAMAÇÃO: "{complaint}"

Retorne APENAS um objeto JSON no formato abaixo, sem qualquer texto antes ou depois:
{{
  "title": "IMP-XXXXX: [Título técnico curto]",
  "description": "[Descrição técnica focada em refatoração/otimização]",
  "details": "[Detalhamento de quais arquivos editar e técnicas de engenharia a usar]",
  "motivation_justification": "[Justificativa técnica baseada na dor do usuário]",
  "category": "[Performance | RAG | UI/UX | Telegram | Segurança | DevOps | Arquitetura]",
  "priority": "[high | medium | low]",
  "difficulty": "[easy | medium | hard]",
  "impact": "[high | medium | low]"
}}"""

    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "gemma2-9b-it",
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                },
                timeout=15
            )
            if r.status_code == 200:
                return json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception:
            pass

    # Fallback Ollama Local
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4-fast:latest",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3}
            },
            timeout=60
        )
        if r.status_code == 200:
            res_text = r.json()["response"]
            import re
            match = re.search(r'\{.*\}', res_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(res_text)
    except Exception as e:
        logging.error(f"Erro ao converter reclamação via LLM local: {e}")
    
    return {
        "title": "IMP-XXXXX: Refatoração sob demanda de usuário",
        "description": f"Tratar reclamação: {complaint}",
        "details": "Analisar arquivos associados para resolver a dor descrita na reclamação.",
        "motivation_justification": f"Feedback direto do usuário: {complaint}",
        "category": "Arquitetura",
        "priority": "medium",
        "difficulty": "medium",
        "impact": "medium"
    }

def call_llm_for_improvements(codebase_context, history_context):
    """Consulta a IA para gerar novas melhorias personalizadas baseadas no código e no histórico."""
    prompt = f"""Você é o Engenheiro de Plataforma da AI Factory. Seu objetivo é propor as próximas melhorias técnicas para o backlog.

---
RESUMO DO CÓDIGO ATUAL:
{codebase_context}

---
ÚLTIMAS MELHORIAS INTEGRADAS:
{history_context}
---

Gere exatamente 21 novas propostas de melhorias altamente específicas, viáveis e relevantes.
Responda APENAS com um array JSON válido de objetos com o seguinte formato:
[
  {{
    "title": "IMP-XXXXX: [Título da melhoria curta]",
    "description": "[Descrição da melhoria]",
    "details": "[Detalhamento técnico]",
    "motivation_justification": "[Justificativa técnica]",
    "category": "[Performance | RAG | UI/UX | Telegram | Segurança | DevOps | Arquitetura]",
    "priority": "[high | medium | low]",
    "difficulty": "[easy | medium | hard]",
    "impact": "[high | medium | low]"
  }}
]"""

    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gemma4-fast:latest",
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.3}
            },
            timeout=120
        )
        if r.status_code == 200:
            res_text = r.json()["response"]
            import re
            match = re.search(r'\[.*\]', res_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(res_text)
    except Exception as e:
        logging.error(f"Erro ao consultar ou decodificar LLM local: {e}")
    
    return []

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    # 1. Abre o backlog atual
    if os.path.exists(IMPROVEMENTS_FILE):
        with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
            backlog = json.load(f)
    else:
        backlog = []

    # 2. Processa feedbacks pendentes do Usuário Chato
    new_tasks_from_feedback = []
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
        except Exception:
            feedbacks = []

        pending_feedbacks = [fb for fb in feedbacks if fb.get("status") == "pending"]
        
        for fb in pending_feedbacks:
            complaint = fb["complaint"]
            # Verifica se já está no backlog (desduplicação)
            is_duplicate = check_is_duplicate(backlog, complaint)
            
            if is_duplicate:
                fb["status"] = "duplicate"
                logging.info(f"Feedback descartado por duplicidade: '{complaint}'")
            else:
                # Transforma a reclamação em card do backlog
                task_data = convert_complaint_to_task(complaint)
                if task_data:
                    new_tasks_from_feedback.append(task_data)
                    fb["status"] = "accepted"
                    logging.info(f"Feedback aceito e convertido em card: '{complaint}'")
                else:
                    fb["status"] = "failed"

        # Salva o arquivo de feedbacks atualizado com os novos status
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)

    # 3. Encontra o último ID
    active_backlog = [t for t in backlog if t["status"] in ["in_progress", "done"]]
    todo_backlog = [t for t in backlog if t["status"] == "todo" and t.get("qualified") is True]
    
    last_id = 0
    for t in backlog:
        try:
            num = int(t["id"].split("-")[-1])
            if num > last_id:
                last_id = num
        except Exception:
            pass

    # 4. Formata e insere novas tarefas oriundas dos feedbacks do Usuário Chato
    formatted_feedback_tasks = []
    for idx, task in enumerate(new_tasks_from_feedback, start=1):
        next_id = f"IMP-{(last_id + idx):05d}"
        formatted_task = {
            "id": next_id,
            "title": f"{next_id}: {task.get('title', '').split(': ', 1)[-1]}",
            "description": task.get("description", "Ajuste sob feedback de usuário."),
            "details": task.get("details", ""),
            "motivation_justification": task.get("motivation_justification", ""),
            "category": task.get("category", "Performance"),
            "status": "todo",
            "priority": task.get("priority", "high"), # Feedback de usuário ganha prioridade alta!
            "difficulty": task.get("difficulty", "medium"),
            "impact": task.get("impact", "medium"),
            "qualified": True,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        formatted_feedback_tasks.append(formatted_task)
        logging.info(f"Nova tarefa adicionada ao TODO via feedback: {next_id} - {formatted_task['title']}")

    # Se não temos feedbacks ativos para preencher o TODO, mantemos a geração dinâmica tradicional
    # Garantindo que a fila TODO tenha sempre exatamente 21 tarefas qualificadas
    total_todo = len(todo_backlog) + len(formatted_feedback_tasks)
    needed = 21 - total_todo

    formatted_new_tasks = []
    if needed > 0:
        logging.info(f"O TODO possui {total_todo} tarefas. Gerando mais {needed} tarefas dinâmicas...")
        codebase_context = get_codebase_summary()
        history_context = get_recent_improvements()
        new_llm_tasks = call_llm_for_improvements(codebase_context, history_context)
        
        last_id += len(formatted_feedback_tasks)
        for idx, task in enumerate(new_llm_tasks[:needed], start=1):
            next_id = f"IMP-{(last_id + idx):05d}"
            formatted_task = {
                "id": next_id,
                "title": f"{next_id}: {task.get('title', '').split(': ', 1)[-1]}",
                "description": task.get("description", "Melhoria dinâmica gerada."),
                "details": task.get("details", ""),
                "motivation_justification": task.get("motivation_justification", ""),
                "category": task.get("category", "Performance"),
                "status": "todo",
                "priority": task.get("priority", "medium"),
                "difficulty": task.get("difficulty", "medium"),
                "impact": task.get("impact", "medium"),
                "qualified": True,
                "created_at": datetime.now().isoformat(),
                "completed_at": None
            }
            formatted_new_tasks.append(formatted_task)

    # Consolida a base: mantemos in_progress/done + os todos qualificados + os novos do feedback + os novos da LLM
    final_backlog = active_backlog + todo_backlog + formatted_feedback_tasks + formatted_new_tasks

    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_backlog, f, ensure_ascii=False, indent=2)

    logging.info(f"Backlog dinâmico atualizado. Total TODO: {len(todo_backlog) + len(formatted_feedback_tasks) + len(formatted_new_tasks)}")

if __name__ == '__main__':
    main()
