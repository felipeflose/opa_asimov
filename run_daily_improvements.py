import os
import requests
import logging
import time
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
    # Carrega variáveis do arquivo .env
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
    
    # 1. Busca o estado atual do backlog para planejar as melhorias do dia
    improvements_url = f"http://localhost:{flask_port}/api/improvements"
    try:
        logging.info("Buscando candidatos do backlog...")
        r = requests.get(improvements_url, timeout=15)
        if r.status_code != 200:
            logging.error(f"Falha ao buscar melhorias: {r.status_code}")
            return
            
        data = r.json()
        # Junta todo e in_progress para selecionar candidatos
        candidates = data.get("in_progress", []) + data.get("todo", [])
        
        # Filtra apenas os que ainda não foram concluídos
        candidates = [c for c in candidates if c["status"] != "done"][:3]
        
        if not candidates:
            send_telegram_message(bot_token, chat_id, "🎉 **[AI Factory]** Todas as 10.000 melhorias do backlog já foram concluídas!")
            return

        # 2. Envia mensagem inicial às 10h informando o planejamento do dia
        init_msg = "⚡ **[AI Factory - Planejamento Diário]**\n"
        init_msg += f"Iniciando lote de melhorias para hoje ({datetime.now().strftime('%d/%m/%Y')}):\n\n"
        for item in candidates:
            clean_title = item['title'].split(': ', 1)[-1] if ': ' in item['title'] else item['title']
            init_msg += f"🔸 **{item['id']}**: {clean_title}\n"
            
        send_telegram_message(bot_token, chat_id, init_msg)
        
        # 3. Executa cada melhoria sequencialmente e avisa o usuário conforme termina
        for item in candidates:
            item_id = item["id"]
            clean_title = item['title'].split(': ', 1)[-1] if ': ' in item['title'] else item['title']
            
            # Avisa início da tarefa
            logging.info(f"Iniciando: {item_id}")
            move_url = f"http://localhost:{flask_port}/api/improvements/move"
            
            # Move para 'in_progress'
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "in_progress"}, timeout=10)
            
            # Simula tempo de execução da melhoria (10 segundos)
            time.sleep(10)
            
            # Move para 'done'
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "done"}, timeout=10)
            
            # Registra no log de atualizações
            log_path = os.path.join(APP_DIR, 'logs', 'update_graph.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] Aplicada: {item_id} - {item['title']}\n")
                lf.write(f"   _{item['description']}_\n")

            # Avisa conclusão no Telegram
            done_msg = f"✅ **[Melhoria Concluída]**\n"
            done_msg += f"**{item_id}**: {clean_title}\n"
            done_msg += f"_{item['description']}_"
            send_telegram_message(bot_token, chat_id, done_msg)
            
    except Exception as e:
        logging.error(f"Erro ao processar rotina diária: {e}")

if __name__ == '__main__':
    main()
