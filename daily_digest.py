import os
import json
import requests
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

APP_DIR      = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_FILE = os.path.join(APP_DIR, 'user_feedback.json')
BACKLOG_FILE  = os.path.join(APP_DIR, 'improvement_backlog.json')
RUN_LOG_FILE  = os.path.join(APP_DIR, 'improvements_run_log.txt')
CYCLE_LOG     = os.path.join(APP_DIR, 'logs', 'factory_cycles.json')
MYSTERY_LOG   = os.path.join(APP_DIR, 'logs', 'mystery_client.log')


def send_telegram(bot_token, chat_id, text):
    if not bot_token or not chat_id:
        logging.warning("Telegram não configurado (TELEGRAM_BOT_TOKEN / FLOSE_NOTIFICATION_CHAT_ID).")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
        logging.info("Relatório enviado com sucesso ao Telegram.")
    except Exception as e:
        logging.error(f"Erro ao enviar Telegram: {e}")


def count_cycles_today():
    if not os.path.exists(CYCLE_LOG):
        return 0, 0
    try:
        with open(CYCLE_LOG) as f:
            cycles = json.load(f)
        today = date.today().isoformat()
        today_cycles = [c for c in cycles if c.get("ts", "").startswith(today)]
        done  = sum(1 for c in today_cycles if c.get("status") == "done")
        total = len(today_cycles)
        return done, total
    except Exception:
        return 0, 0


def count_feedbacks_today():
    if not os.path.exists(FEEDBACK_FILE):
        return 0, 0, 0
    try:
        with open(FEEDBACK_FILE) as f:
            feedbacks = json.load(f)
        today = date.today().isoformat()
        today_fbs = [fb for fb in feedbacks if fb.get("timestamp", "").startswith(today)]
        total     = len(today_fbs)
        accepted  = sum(1 for fb in today_fbs if fb.get("status") == "accepted")
        duplicate = sum(1 for fb in today_fbs if fb.get("status") == "duplicate")
        return total, accepted, duplicate
    except Exception:
        return 0, 0, 0


def count_improvements_today():
    if not os.path.exists(RUN_LOG_FILE):
        return [], 0
    today = date.today().isoformat()
    items, tests_failed = [], 0
    try:
        with open(RUN_LOG_FILE) as f:
            lines = f.readlines()
        for line in lines:
            if today in line and "[AUTO-IMPROVEMENT]" in line:
                items.append(line.strip())
            if today in line and "FALHARAM" in line:
                tests_failed += 1
    except Exception:
        pass
    return items, tests_failed


def count_mystery_today():
    if not os.path.exists(MYSTERY_LOG):
        return 0
    today = date.today().isoformat()
    count = 0
    try:
        with open(MYSTERY_LOG) as f:
            for line in f:
                if today in line and "aplicada" in line.lower():
                    count += 1
    except Exception:
        pass
    return count


def backlog_stats():
    if not os.path.exists(BACKLOG_FILE):
        return 0, 0, 0
    try:
        with open(BACKLOG_FILE) as f:
            bl = json.load(f)
        todo = sum(1 for t in bl if t.get("status") == "todo")
        wip  = sum(1 for t in bl if t.get("status") == "in_progress")
        done = sum(1 for t in bl if t.get("status") == "done")
        return todo, wip, done
    except Exception:
        return 0, 0, 0


def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(APP_DIR, '.env'))

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id   = os.environ.get("FLOSE_NOTIFICATION_CHAT_ID", "2128622574")

    today_fmt = datetime.now().strftime('%d/%m/%Y')
    now_fmt   = datetime.now().strftime('%H:%M')

    cycles_done, cycles_total     = count_cycles_today()
    fb_total, fb_accept, fb_dup   = count_feedbacks_today()
    improvements, qa_failures     = count_improvements_today()
    mystery_count                 = count_mystery_today()
    bl_todo, bl_wip, bl_done      = backlog_stats()

    # ── MONTA RELATÓRIO ─────────────────────────────────────
    lines = []
    lines.append(f"📅 <b>AI Factory — Relatório Diário {today_fmt}</b>")
    lines.append(f"<i>Expediente 09h00 → 18h00 | Gerado às {now_fmt}</i>")
    lines.append("")

    # Ciclos
    lines.append("🔄 <b>Ciclos executados hoje</b>")
    lines.append(f"  • Ciclos totais: <b>{cycles_total}</b>")
    lines.append(f"  • Concluídos com sucesso: <b>{cycles_done}</b>")
    lines.append("")

    # Melhorias codadas
    lines.append("🛠️ <b>Melhorias implementadas & comitadas na main</b>")
    if improvements:
        for imp in improvements[-5:]:          # últimas 5 para não explodir o tamanho
            tag = imp.split("Aplicada:")[-1].strip() if "Aplicada:" in imp else imp
            lines.append(f"  🔸 {tag[:80]}")
    else:
        lines.append("  (Nenhuma implementação hoje)")
    if qa_failures:
        lines.append(f"  ⚠️ Ciclos rejeitados pelo QA (pytest): <b>{qa_failures}</b>")
    lines.append("")

    # QA
    lines.append("🧪 <b>Pipeline QA</b>")
    qa_pass = len(improvements)
    lines.append(f"  • Builds aprovados pelo QA: <b>{qa_pass}</b>")
    lines.append(f"  • Builds rejeitados / retrabalho: <b>{qa_failures}</b>")
    lines.append("")

    # Feedbacks
    lines.append("🤬 <b>Feedbacks dos Usuários</b>")
    lines.append(f"  • Reclamações recebidas: <b>{fb_total}</b>")
    lines.append(f"  • Aceitas → viraram card: <b>{fb_accept}</b>")
    lines.append(f"  • Descartadas (duplicadas): <b>{fb_dup}</b>")
    lines.append("")

    # Cliente Oculto
    lines.append("🕵️ <b>Cliente Oculto (Chaos Monkey)</b>")
    lines.append(f"  • Refatorações silenciosas aplicadas: <b>{mystery_count}</b>")
    lines.append("")

    # Estado do Backlog
    lines.append("📊 <b>Estado do Backlog</b>")
    lines.append(f"  • TODO: <b>{bl_todo}</b>  |  Em progresso: <b>{bl_wip}</b>  |  Done: <b>{bl_done}</b>")
    lines.append("")

    lines.append("🚀 <i>Tudo entregue automaticamente — sem nenhuma intervenção sua hoje!</i>")

    message = "\n".join(lines)
    send_telegram(bot_token, chat_id, message)


if __name__ == '__main__':
    main()
