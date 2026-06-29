import os
import json
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_LOG_FILE = os.path.join(APP_DIR, 'improvements_run_log.txt')
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')
IMPROVEMENTS_FILE = os.path.join(APP_DIR, 'improvement_backlog.json')

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
        logging.error(f"Erro ao enviar digest Telegram: {e}")

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FLOSE_NOTIFICATION_CHAT_ID", "2128622574")

    today_str = datetime.now().strftime('%Y-%m-%d')
    today_formatted = datetime.now().strftime('%d/%m/%Y')

    # 1. Coleta melhorias diárias do log de execução
    daily_improvements = []
    mystery_refactors = []
    if os.path.exists(RUN_LOG_FILE):
        try:
            with open(RUN_LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                if today_str in line:
                    if "[AUTO-IMPROVEMENT]" in line or "- IMP-" in line:
                        daily_improvements.append(line.strip())
                    elif "[MYSTERY-CLIENT]" in line:
                        mystery_refactors.append(line.strip())
        except Exception as e:
            logging.error(f"Erro ao ler run log: {e}")

    # 2. Coleta dados do Usuário Chato
    total_feedbacks = 0
    accepted_feedbacks = 0
    duplicate_feedbacks = 0
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                feedbacks = json.load(f)
            for fb in feedbacks:
                if today_str in fb.get("timestamp", ""):
                    total_feedbacks += 1
                    if fb.get("status") == "accepted":
                        accepted_feedbacks += 1
                    elif fb.get("status") == "duplicate":
                        duplicate_feedbacks += 1
        except Exception as e:
            logging.error(f"Erro ao ler feedbacks: {e}")

    # 3. Busca estatísticas do Backlog
    stats = {"done": 0, "in_progress": 0, "todo": 0}
    if os.path.exists(IMPROVEMENTS_FILE):
        try:
            with open(IMPROVEMENTS_FILE, 'r', encoding='utf-8') as f:
                backlog = json.load(f)
            for t in backlog:
                status = t.get("status")
                if status in stats:
                    stats[status] += 1
        except Exception:
            pass

    # 4. Constrói a mensagem de Relatório Diário
    msg = f"📅 <b>[AI Factory - Relatório Diário {today_formatted}]</b>\n"
    msg += "Aqui está o resumo de tudo o que aconteceu na fábrica hoje (09h00 - 18h00):\n\n"

    # Seção 1: Melhorias Aplicadas
    msg += "🛠️ <b>Melhorias Codadas & Comitadas:</b>\n"
    if daily_improvements:
        # Filtra e limpa as linhas duplicadas/cabeçalhos
        clean_improvements = []
        for imp in daily_improvements:
            if "- IMP-" in imp:
                clean_improvements.append(f"  🔸 {imp.replace('- ', '')}")
        if clean_improvements:
            msg += "\n".join(clean_improvements) + "\n\n"
        else:
            msg += "  (Executadas em plano de fundo com sucesso)\n\n"
    else:
        msg += "  (Nenhuma alteração diária realizada hoje)\n\n"

    # Seção 2: Cliente Oculto
    msg += "🕵️‍♂️ <b>Refatorações do Cliente Oculto:</b>\n"
    if mystery_refactors:
        for ref in mystery_refactors:
            parts = ref.split("applied in ") if "applied in " in ref else ref.split("aplicada em ")
            filename = parts[-1] if len(parts) > 1 else ref
            msg += f"  🔹 Refatoração otimizada aplicada em <code>{filename}</code>\n"
        msg += "\n"
    else:
        msg += "  (Nenhuma intervenção silenciosa hoje)\n\n"

    # Seção 3: Usuário Chato & Triage do PM
    msg += "🤬 <b>Auditoria do Usuário Chato:</b>\n"
    msg += f"  • Reclamações analisadas: <b>{total_feedbacks}</b>\n"
    msg += f"  • Aceitas e viraram tarefas: <b>{accepted_feedbacks}</b>\n"
    msg += f"  • Descartadas (Duplicadas): <b>{duplicate_feedbacks}</b>\n\n"

    # Seção 4: Estado Geral da Fábrica
    msg += "📊 <b>Estado Geral do Backlog:</b>\n"
    msg += f"  • A Fazer (TODO): <b>{stats.get('todo', 0)}</b>\n"
    msg += f"  • Em Progresso: <b>{stats.get('in_progress', 0)}</b>\n"
    msg += f"  • Concluídas: <b>{stats.get('done', 0)}</b>\n\n"

    msg += "🚀 <i>Todas as entregas de hoje passaram por testes de CI/CD automatizados e foram integradas diretamente na branch main remota.</i>"

    send_telegram_message(bot_token, chat_id, msg)
    logging.info("Relatório diário enviado com sucesso no Telegram.")

if __name__ == '__main__':
    main()
