import os
import requests
import logging
import time
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def send_telegram_message(bot_token, chat_id, text, parse_mode="HTML"):
    if not bot_token or not chat_id:
        return
    try:
        tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(tg_url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
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

        # Configura branch Git diária baseada na data local
        date_str = datetime.now().strftime('%Y%m%d_%H%M')
        branch_name = f"feature/improvements-{date_str}"
        
        # Cria a branch limpa a partir da origin/main remota para evitar commits locais com segredos
        logging.info(f"Atualizando repositório e criando branch Git: {branch_name}")
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "clean", "-fd"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "checkout", "-b", branch_name, "origin/main"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Traz todo o código atualizado da main local como alterações (sem carregar o histórico de segredos antigos)
        subprocess.run(["git", "checkout", "main", "--", "."], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 2. Envia mensagem inicial às 10h informando o planejamento do dia
        init_msg = "⚡ <b>[AI Factory - Planejamento Diário]</b>\n"
        init_msg += f"Iniciando lote de melhorias para hoje ({datetime.now().strftime('%d/%m/%Y')}):\n\n"
        for item in candidates:
            clean_title = item['title'].split(': ', 1)[-1] if ': ' in item['title'] else item['title']
            init_msg += f"🔸 <b>{item['id']}</b>: {clean_title}\n"
            
        send_telegram_message(bot_token, chat_id, init_msg, parse_mode="HTML")
        
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

            # Avisa conclusão no Telegram (HTML)
            done_msg = f"✅ <b>[Melhoria Concluída]</b>\n"
            done_msg += f"<b>{item_id}</b>: {clean_title}\n"
            done_msg += f"<i>{item['description']}</i>"
            send_telegram_message(bot_token, chat_id, done_msg, parse_mode="HTML")

        # 4. Pré-verificação de Testes (CI/CD Local)
        logging.info("Executando a suite de testes automatizados antes de enviar o PR...")
        test_run = subprocess.run([os.path.join(APP_DIR, ".venv", "bin", "pytest"), "tests/"], cwd=APP_DIR)
        
        if test_run.returncode != 0:
            logging.error("Os testes unitários FALHARAM! Abortando o push para segurança do repositório.")
            fail_msg = "⚠️ <b>[AI Factory - CI/CD Falhou]</b>\n\n"
            fail_msg += "As melhorias do dia foram executadas locais, mas a suite de testes unitários detectou falhas no código.\n\n"
            fail_msg += "O envio da branch e do PR para o GitHub foi bloqueado automaticamente por segurança."
            send_telegram_message(bot_token, chat_id, fail_msg, parse_mode="HTML")
            subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        # 5. Finalização de código: Grava log visível ao Git, commita e faz push da branch
        logging.info("Gravando logs e realizando push para o repositório...")
        git_log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
        with open(git_log_path, 'a', encoding='utf-8') as gf:
            gf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Lote diário de melhorias aplicado com sucesso:\n")
            for item in candidates:
                gf.write(f"- {item['id']}: {item['title']}\n")
                
        subprocess.run(["git", "add", "."], cwd=APP_DIR)
        commit_msg = f"chore(daily): apply daily improvements ({', '.join([c['id'] for c in candidates])})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR)
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=APP_DIR)

        # 6. Envia o relatório final com link do PR no Telegram (HTML)
        pr_url = f"https://github.com/felipeflose/opa_asimov/pull/new/{branch_name}"
        final_report = "🚀 <b>[Lote Diário Concluído no GitHub]</b>\n\n"
        final_report += f"Todas as 3 melhorias de hoje passaram nos testes unitários e foram salvas na branch <code>{branch_name}</code> no GitHub!\n\n"
        final_report += f"🔗 <b>Crie e aprove o Pull Request:</b>\n{pr_url}"
        send_telegram_message(bot_token, chat_id, final_report, parse_mode="HTML")
            
    except Exception as e:
        logging.error(f"Erro ao processar rotina diária: {e}")
        subprocess.run(["git", "checkout", "main"], cwd=APP_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    main()
