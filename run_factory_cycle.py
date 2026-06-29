import os
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    logging.info("=== [CICLO INICIADO] Iniciando ciclo completo da AI Factory ===")
    
    # 1. Roda o Usuário Chato para testar e gerar feedbacks
    logging.info("1. Acionando Usuário Chato (Simulação de uso & Auditoria)...")
    subprocess.run([os.path.join(APP_DIR, ".venv", "bin", "python3"), os.path.join(APP_DIR, "annoying_user.py")], cwd=APP_DIR)
    
    # 2. Roda o PM para triar reclamações e atualizar backlog
    logging.info("2. Acionando Product Manager (Triagem de Backlog)...")
    subprocess.run([os.path.join(APP_DIR, ".venv", "bin", "python3"), os.path.join(APP_DIR, "generate_dynamic_backlog.py")], cwd=APP_DIR)
    
    # 3. Roda o Dev para codificar as melhorias pendentes
    logging.info("3. Acionando Dev Agent (Implementação, Testes e Commit)...")
    subprocess.run([os.path.join(APP_DIR, ".venv", "bin", "python3"), os.path.join(APP_DIR, "run_daily_improvements.py")], cwd=APP_DIR)
    
    logging.info("=== [CICLO CONCLUÍDO] Ciclo da AI Factory finalizado com sucesso! ===")

if __name__ == '__main__':
    main()
