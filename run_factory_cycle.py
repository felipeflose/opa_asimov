import os
import json
import subprocess
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CYCLE_LOG = os.path.join(APP_DIR, 'logs', 'factory_cycles.json')

WORK_START = 9   # 09:00
WORK_END   = 18  # 18:00 (exclusivo — não roda às 18h em diante)

def within_business_hours():
    now = datetime.now()
    return WORK_START <= now.hour < WORK_END

def log_cycle(status, details=""):
    os.makedirs(os.path.dirname(CYCLE_LOG), exist_ok=True)
    cycles = []
    if os.path.exists(CYCLE_LOG):
        try:
            with open(CYCLE_LOG, 'r') as f:
                cycles = json.load(f)
        except Exception:
            cycles = []
    cycles.append({
        "ts": datetime.now().isoformat(),
        "status": status,
        "details": details
    })
    with open(CYCLE_LOG, 'w') as f:
        json.dump(cycles, f, ensure_ascii=False, indent=2)

def main():
    if not within_business_hours():
        logging.info(f"Fora do horário comercial ({WORK_START}h–{WORK_END}h). Ciclo ignorado.")
        return

    logging.info("=== [CICLO INICIADO] AI Factory — Horário Comercial Ativo ===")
    log_cycle("started")

    py = os.path.join(APP_DIR, ".venv", "bin", "python3")

    # 1. Usuário Chato — gera feedbacks reais
    logging.info("1. Usuário Chato (auditoria de uso)...")
    subprocess.run([py, os.path.join(APP_DIR, "annoying_user.py")], cwd=APP_DIR)

    # 2. PM — tria, deduplicação e popula backlog
    logging.info("2. PM Agent (triagem e backlog)...")
    subprocess.run([py, os.path.join(APP_DIR, "generate_dynamic_backlog.py")], cwd=APP_DIR)

    # 3. Dev — codifica, passa pelo QA (pytest) e comita na main
    logging.info("3. Dev Agent (implementação + QA + commit)...")
    subprocess.run([py, os.path.join(APP_DIR, "run_daily_improvements.py")], cwd=APP_DIR)

    logging.info("=== [CICLO CONCLUÍDO] ===")
    log_cycle("done")

if __name__ == '__main__':
    main()
