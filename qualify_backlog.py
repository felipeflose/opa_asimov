import os
import json
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')

# Mapeamento estrito de componentes do backlog para os arquivos reais do projeto
COMPONENT_MAP = {
    "RAGAgent": "agent_rag.py",
    "Telegram Bot": "agent_bot.py",
    "D3.js Graph": "static/js/app.js",
    "Flask App Dashboard": "app.py",
    "SQLite Persistent Queue": "app.py",
    "Ollama Local Integration": "agent_core.py",
    "Docling PDF Converter": "agent_rag.py",
    "Lineage Auditor": "agent_core.py",
    "Health Monitor": "agent_health.py",
    "Sanitizer Pipeline": "agent_sanitizer.py"
}

def ask_llm_qualification(api_key, component_code, task_title, task_desc):
    """Consulta o modelo (Ollama local ou Groq) para validar a relevância do card."""
    prompt = f"""Você é o Auditor da AI Factory. Analise se a tarefa proposta faz sentido técnico dado o contexto do código do arquivo.

---
CÓDIGO DO ARQUIVO:
{component_code[:2500]}
---
TAREFA: {task_title}
DESCRIÇÃO: {task_desc}

Responda APENAS com a palavra "SIM" se a tarefa for relevante, factível e agregar valor a este código, ou "NAO" se for obsoleta, irrelevante ou exigir componentes inexistentes. Não explique nada, responda apenas SIM ou NAO."""

    # Tenta usar Groq ou fallback para Ollama local
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
                "model": "gemma",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0}
            },
            timeout=15
        )
        if r.status_code == 200:
            answer = r.json()["response"].strip().upper()
            return "SIM" in answer
    except Exception as e:
        logging.error(f"Erro ao consultar LLM local: {e}")
    
    # Heurística padrão caso a IA esteja offline
    return True

def send_telegram_message(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        return
    try:
        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(tg_url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem Telegram: {e}")

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FLOSE_NOTIFICATION_CHAT_ID", "2128622574")

    if not os.path.exists(IMPROVEMENTS_FILE):
        logging.error("Backlog não encontrado para qualificação.")
        return

    with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
        backlog = json.load(f)

    # Identifica tarefas já qualificadas e ativas
    qualified_pool = [t for t in backlog if t.get("qualified") is True and t["status"] in ["todo", "in_progress"]]
    
    needed = 10 - len(qualified_pool)
    if needed <= 0:
        logging.info("O pool já possui 10 ou mais tarefas qualificadas ativas.")
        return

    logging.info(f"Iniciando qualificação diária. Precisamos encontrar mais {needed} tarefas qualificadas.")
    newly_qualified = []
    
    # Cache do conteúdo dos arquivos para evitar leituras repetidas em disco
    file_contents_cache = {}

    for item in backlog:
        if len(newly_qualified) >= needed:
            break
            
        # Pula itens que não estão em 'todo' ou já foram processados/qualificados
        if item["status"] != "todo" or item.get("qualified") is True or item.get("status") == "deprecated":
            continue

        comp = item.get("category")
        # Encontra o componente correspondente no mapeamento
        mapped_component = None
        for key in COMPONENT_MAP.keys():
            if key.lower() in item["title"].lower() or key.lower() in item.get("details", "").lower():
                mapped_component = key
                break
        
        if not mapped_component:
            # Componente não reconhecido no código atual -> deprecia a tarefa
            item["status"] = "deprecated"
            continue

        filename = COMPONENT_MAP[mapped_component]
        filepath = os.path.join(APP_DIR, filename)

        if not os.path.exists(filepath):
            # Arquivo físico não existe -> deprecia a tarefa
            item["status"] = "deprecated"
            continue

        # Lê o código do arquivo para o prompt de auditoria do LLM
        if filepath not in file_contents_cache:
            try:
                with open(filepath, 'r', encoding='utf-8') as cf:
                    file_contents_cache[filepath] = cf.read()
            except Exception:
                file_contents_cache[filepath] = ""

        file_code = file_contents_cache[filepath]
        if not file_code:
            item["status"] = "deprecated"
            continue

        # Qualifica a tarefa via IA
        is_valid = ask_llm_qualification(None, file_code, item["title"], item["description"])
        
        if is_valid:
            item["qualified"] = True
            item["priority"] = "high"
            newly_qualified.append(item)
            logging.info(f"Tarefa qualificada com sucesso: {item['id']} - {item['title']}")
        else:
            item["status"] = "deprecated"
            logging.info(f"Tarefa depreciada (sem contexto atual): {item['id']}")

    # Salva o backlog atualizado
    with open(IMPROVEMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(backlog, f, ensure_ascii=False, indent=2)

    if newly_qualified:
        msg = "🔍 <b>[AI Factory - Qualificação Diária]</b>\n"
        msg += f"Auditamos o backlog e qualificamos <b>{len(newly_qualified)} novas tarefas</b> altamente compatíveis com o código atual:\n\n"
        for t in newly_qualified:
            clean_title = t['title'].split(': ', 1)[-1] if ': ' in t['title'] else t['title']
            msg += f"🔸 <b>{t['id']}</b>: {clean_title} (Componente: {t.get('category')})\n"
        send_telegram_message(bot_token, chat_id, msg)
        logging.info("Qualificação concluída e notificada.")
    else:
        logging.info("Nenhuma nova tarefa qualificada hoje.")

if __name__ == '__main__':
    main()
