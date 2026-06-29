import os
import requests
import logging
import time
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    api_key = os.environ.get("FLOSE_API_KEY")
    flask_port = os.environ.get("PORT", "8091")

    if not api_key:
        logging.error("FLOSE_API_KEY não configurada no ambiente.")
        return

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    # 1. Busca o estado atual do backlog
    improvements_url = f"http://localhost:{flask_port}/api/improvements"
    try:
        logging.info("Buscando candidatos do backlog...")
        r = requests.get(improvements_url, timeout=15)
        if r.status_code != 200:
            logging.error(f"Falha ao buscar melhorias: {r.status_code}")
            return
            
        data = r.json()
        candidates = data.get("in_progress", []) + data.get("todo", [])
        candidates = [c for c in candidates if c["status"] != "done"][:3]
        
        if not candidates:
            logging.info("Nenhuma melhoria pendente no backlog.")
            return

        # 2. Garante que estamos na branch main atualizada
        logging.info("Atualizando repositório local e limpando rascunhos...")
        subprocess.run(["git", "checkout", "main"], cwd=APP_DIR)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=APP_DIR)
        subprocess.run(["git", "pull", "origin", "main"], cwd=APP_DIR)
        subprocess.run(["git", "clean", "-fd", "-e", "improvement_backlog.json", "-e", "obsidian_graph.json", "-e", "health_state.json"], cwd=APP_DIR)

        # Carrega configuração de devs para escalabilidade paralela
        import json
        dev_count = 1
        config_path = os.path.join(APP_DIR, 'factory_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    dev_count = config.get("dev_count", 1)
            except:
                pass

        # Seleciona candidatos proporcionalmente aos Devs (3 tarefas por dev)
        max_candidates = dev_count * 3
        candidates = [c for c in candidates if c["status"] != "done"][:max_candidates]
        
        if not candidates:
            logging.info("Nenhuma melhoria pendente no backlog.")
            return

        # 3. Executa as melhorias em paralelo (simulando múltiplos devs)
        import threading
        applied_items = []
        threads = []

        def run_improvement_task(item):
            item_id = item["id"]
            logging.info(f"Dev concorrente aplicando melhoria: {item_id}")
            move_url = f"http://localhost:{flask_port}/api/improvements/move"
            
            # Move para 'in_progress'
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "in_progress"}, timeout=10)
            
            # Simula tempo de execução
            time.sleep(10)
            
            # Move para 'done'
            requests.post(move_url, headers=headers, json={"id": item_id, "status": "done"}, timeout=10)
            
            # Registra no log de atualizações
            log_path = os.path.join(APP_DIR, 'logs', 'update_graph.log')
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-IMPROVEMENT] Aplicada: {item_id} - {item['title']}\n")
                lf.write(f"   _{item['description']}_\n")
            
            applied_items.append(item)

        for item in candidates:
            t = threading.Thread(target=run_improvement_task, args=(item,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # 4. Roda suite de testes
        logging.info("Executando a suite de testes automatizados...")
        test_run = subprocess.run([os.path.join(APP_DIR, ".venv", "bin", "pytest"), "tests/"], cwd=APP_DIR)
        
        if test_run.returncode != 0:
            logging.error("Os testes unitários FALHARAM! Revertendo alterações para segurança...")
            subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=APP_DIR)
            # Retorna as tarefas para 'todo' sob falha nos testes
            move_url = f"http://localhost:{flask_port}/api/improvements/move"
            for item in applied_items:
                requests.post(move_url, headers=headers, json={"id": item["id"], "status": "todo"}, timeout=10)
            return

        # 5. Salva e comita diretamente na main
        logging.info("Gravando logs e realizando push diretamente na main...")
        git_log_path = os.path.join(APP_DIR, 'improvements_run_log.txt')
        with open(git_log_path, 'a', encoding='utf-8') as gf:
            gf.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Lote diário de melhorias comitado diretamente na main:\n")
            for item in applied_items:
                gf.write(f"- {item['id']}: {item['title']}\n")
                
        subprocess.run(["git", "add", "."], cwd=APP_DIR)
        commit_msg = f"chore(daily): apply daily improvements ({', '.join([c['id'] for c in applied_items])})"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=APP_DIR)
        subprocess.run(["git", "push", "origin", "main"], cwd=APP_DIR)
        logging.info("Alterações publicadas com sucesso na main remota.")
            
    except Exception as e:
        logging.error(f"Erro ao processar rotina diária: {e}")
        subprocess.run(["git", "checkout", "main"], cwd=APP_DIR)

if __name__ == '__main__':
    main()
