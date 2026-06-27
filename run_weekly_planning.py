import os
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def send_telegram_message(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        return
    try:
        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(tg_url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem Telegram: {e}")

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    api_key = os.environ.get("FLOSE_API_KEY")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FLOSE_NOTIFICATION_CHAT_ID", "2128622574")
    flask_port = os.environ.get("PORT", "8091")

    if not api_key:
        logging.error("FLOSE_API_KEY não configurada no ambiente.")
        return

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    # 1. Busca melhorias atuais
    improvements_url = f"http://localhost:{flask_port}/api/improvements"
    try:
        r = requests.get(improvements_url, timeout=15)
        if r.status_code != 200:
            return
            
        data = r.json()
        todos = data.get("todo", [])
        
        # Seleciona 21 tarefas para a semana (3 por dia)
        weekly_tasks = [t for t in todos if t["status"] == "todo"][:21]
        
        if not weekly_tasks:
            send_telegram_message(bot_token, chat_id, "📅 **[AI Factory - Planning Semanal]** Nenhuma tarefa pendente no backlog!")
            return
            
        # Move tarefas para 'in_progress'
        move_url = f"http://localhost:{flask_port}/api/improvements/move"
        for t in weekly_tasks:
            requests.post(move_url, headers=headers, json={"id": t["id"], "status": "in_progress"}, timeout=10)
            
        # Envia notificação
        msg = "📅 **[AI Factory - Planning Semanal]**\n"
        msg += f"Iniciando a semana de {datetime.now().strftime('%d/%m/%Y')} com **{len(weekly_tasks)} melhorias** selecionadas:\n\n"
        for t in weekly_tasks:
            clean_title = t['title'].split(': ', 1)[-1] if ': ' in t['title'] else t['title']
            msg += f"🔹 **{t['id']}** (Prioridade: {t.get('priority', 'medium').upper()}): {clean_title}\n"
            
        send_telegram_message(bot_token, chat_id, msg)
        logging.info("Planning semanal executado e notificado com sucesso.")
        
    except Exception as e:
        logging.error(f"Erro no planning semanal: {e}")

if __name__ == '__main__':
    main()
