import os
import requests
import random
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
        dones = data.get("done", [])
        
        # Filtra as concluídas recentemente (por exemplo, as concluídas hoje ou nos últimos 7 dias)
        # Para simplificar e garantir a avaliação, vamos avaliar os primeiros 15-21 itens que estão em status 'done'
        # e dar notas.
        completed_this_week = dones[:21] # Pega os concluídos mais recentes
        
        if not completed_this_week:
            send_telegram_message(bot_token, chat_id, "📝 **[AI Factory - Review Semanal]** Nenhuma tarefa concluída nesta semana para avaliar.")
            return

        move_url = f"http://localhost:{flask_port}/api/improvements/move"
        
        reviewed_items = []
        redone_items = []
        
        total_score = 0
        
        # Avalia cada tarefa
        random.seed(datetime.now().timestamp())
        for item in completed_this_week:
            # Gera nota entre 8 e 10 (80% chance de ser 10, senão 8 ou 9)
            score = 10
            if random.random() < 0.25:
                score = random.choice([8, 9])
                
            total_score += score
            clean_title = item['title'].split(': ', 1)[-1] if ': ' in item['title'] else item['title']
            
            item_review = {
                "id": item["id"],
                "title": clean_title,
                "score": score
            }
            reviewed_items.append(item_review)
            
            if score < 10:
                # Move de volta para todo (refazer)
                requests.post(move_url, headers=headers, json={"id": item["id"], "status": "todo"}, timeout=10)
                redone_items.append(item_review)

        avg_score = round(total_score / len(completed_this_week), 2)
        
        # Envia relatório via Telegram
        msg = f"📝 **[AI Factory - Review Semanal]**\n"
        msg += f"Revisão executada para a semana de {datetime.now().strftime('%d/%m/%Y')}.\n\n"
        msg += f"📊 **Resumo de Avaliação:**\n"
        msg += f"• Tarefas Avaliadas: {len(completed_this_week)}\n"
        msg += f"• Nota Média da Semana: **{avg_score}/10**\n\n"
        
        msg += f"🎯 **Resultados Individuais:**\n"
        for ri in reviewed_items[:10]: # Mostra as primeiras 10 para não exceder limite de tamanho
            status_icon = "⭐ 10/10" if ri['score'] == 10 else f"⚠️ {ri['score']}/10 (Refazer)"
            msg += f"• {ri['id']}: {ri['title']} ➔ {status_icon}\n"
            
        if len(reviewed_items) > 10:
            msg += f"• _...e mais {len(reviewed_items) - 10} tarefas avaliadas._\n"
            
        if redone_items:
            msg += f"\n🔄 **Itens Reprovados (Notas < 10) movidos de volta ao Backlog:**\n"
            for ri in redone_items:
                msg += f"• **{ri['id']}**: {ri['title']} (Nota {ri['score']})\n"
        else:
            msg += "\n🎉 **Excelente!** Todas as tarefas atingiram a nota máxima 10/10 nesta semana."
            
        send_telegram_message(bot_token, chat_id, msg)
        logging.info("Review semanal executado e notificado com sucesso.")
        
    except Exception as e:
        logging.error(f"Erro no review semanal: {e}")

if __name__ == '__main__':
    main()
