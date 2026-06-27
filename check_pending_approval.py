import os
import json
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APPROVAL_FILE = os.path.join(APP_DIR, 'pending_approval.json')

def main():
    # Carrega variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("FLOSE_NOTIFICATION_CHAT_ID", "2128622574")

    if not os.path.exists(APPROVAL_FILE):
        logging.info("Nenhuma aprovação pendente no arquivo local.")
        return

    try:
        with open(APPROVAL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        plan_title = data.get("title", "Alterações no Código")
        
        msg = f"⚠️ **[Lembrete de Aprovação Pendente]**\n\n"
        msg += f"Felipe, o plano de alterações **'{plan_title}'** ainda está aguardando sua revisão e aprovação no cockpit.\n\n"
        msg += "Por favor, acesse o chat para aprovar e permitir o início do desenvolvimento."

        if bot_token and chat_id:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            tg_resp = requests.post(tg_url, json={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            }, timeout=10)
            if tg_resp.status_code == 200:
                logging.info("Notificação de lembrete enviada ao Telegram.")
            else:
                logging.error(f"Erro no envio ao Telegram: {tg_resp.status_code}")
    except Exception as e:
        logging.error(f"Erro ao processar verificação de aprovação: {e}")

if __name__ == '__main__':
    main()
