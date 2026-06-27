import os
import time
import json
import requests
import threading
import logging
from datetime import datetime
import agent_core

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HEALTH_STATE_FILE = os.path.join(APP_DIR, "health_state.json")
OLLAMA_URL = "http://localhost:11434/api/tags"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_CHAT_ID = os.getenv("TELEGRAM_USER_ID") # Adicionar no .env se possível

class HealthMonitor:
    def __init__(self):
        self.ollama_healthy = True
        self.state = self.load_state()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def load_state(self):
        if os.path.exists(HEALTH_STATE_FILE):
            try:
                with open(HEALTH_STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Health: Erro ao ler arquivo de estado: {e}")
        return {"ollama": "online", "components": {}}

    def save_state(self):
        with self.lock:
            try:
                with open(HEALTH_STATE_FILE, 'w') as f:
                    json.dump(self.state, f, indent=2)
            except Exception as e:
                logger.error(f"Health: Erro ao salvar estado: {e}")

    def notify_telegram(self, message):
        if not TELEGRAM_TOKEN:
            logger.warning("Health: TELEGRAM_BOT_TOKEN não configurado, notificação ignorada.")
            return
        chat_id = USER_CHAT_ID
        bot_state_path = os.path.join(APP_DIR, "agent_bot_state.json")
        if not chat_id and os.path.exists(bot_state_path):
            try:
                with open(bot_state_path, 'r') as f:
                    chat_id = json.load(f).get("last_messages", [{}])[0].get("chat_id")
            except Exception as e:
                logger.warning(f"Health: Não foi possível obter chat_id do bot_state: {e}")
        
        if not chat_id:
            logger.warning("Health: USER_CHAT_ID não configurado e nenhum chat_id ativo encontrado no agent_bot_state.json.")
            return
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            logger.error(f"Health: Erro ao notificar Telegram: {e}")

    def _monitor_loop(self):
        logger.info("HealthMonitor: Iniciando loop de monitoramento.")
        import psutil
        import os
        
        while True:
            try:
                # 1. Monitor Flask Process resources
                try:
                    process = psutil.Process(os.getpid())
                    cpu_p = process.cpu_percent(interval=None)
                    mem_info = process.memory_info()
                    mem_rss_gb = mem_info.rss / (1024 ** 3)
                    mem_p = process.memory_percent()
                    
                    self.state["flask_process"] = {
                        "cpu_percent": round(cpu_p, 1),
                        "memory_rss_gb": round(mem_rss_gb, 3),
                        "memory_percent": round(mem_p, 2),
                        "pid": os.getpid(),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Alerta em caso de uso crítico de RAM do processo Flask (>85%)
                    if mem_p > 85:
                        logger.warning(f"Health: Uso crítico de RAM pelo processo Flask (PID {os.getpid()}): {mem_p:.1f}%")
                except Exception as pe:
                    logger.warning(f"Health: Falha ao coletar telemetria do processo Flask: {pe}")

                # 2. Check Ollama
                prev_status = self.ollama_healthy
                try:
                    resp = requests.get(OLLAMA_URL, timeout=5)
                    self.ollama_healthy = resp.status_code == 200
                except Exception as e:
                    logger.debug(f"Health: Falha na conexão com o Ollama: {e}")
                    self.ollama_healthy = False
                
                # 3. Update State
                current_status = "online" if self.ollama_healthy else "offline"
                if current_status != self.state.get("ollama"):
                    self.state["ollama"] = current_status
                    self.state["last_change"] = datetime.now().isoformat()
                    
                    # 4. Notify
                    emoji = "✅" if self.ollama_healthy else "🚨"
                    fallback_msg = " - Fallback para GROQ ativado." if not self.ollama_healthy else " - Restaurando Ollama."
                    self.notify_telegram(f"{emoji} *Status Ollama:* {current_status.upper()}{fallback_msg}")
                    
                self.state["last_check"] = datetime.now().isoformat()
                self.save_state()
                
            except Exception as e:
                logger.error(f"HealthMonitor Error: {e}")
            
            time.sleep(30)

    def is_ollama_alive(self):
        return self.ollama_healthy

# Singleton para ser usado em todo o projeto
monitor = HealthMonitor()

def get_health_status():
    return monitor.is_ollama_alive()
