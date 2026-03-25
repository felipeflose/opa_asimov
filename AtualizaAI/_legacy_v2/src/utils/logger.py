import json
import logging
from datetime import datetime
import os

class FloseLogger:
    def __init__(self, service_name="flose-ai"):
        self.service = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        # Handler para stdout (Cloud Run captura)
        handler = logging.StreamHandler()
        self.logger.addHandler(handler)

    def _log(self, level, event, message, details=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "service": self.service,
            "event": event,
            "message": message,
            "details": details or {}
        }
        # Saída em formato JSON para estruturação no Cloud Logging
        print(json.dumps(log_entry))

    def info(self, event, message, details=None):
        self._log("INFO", event, message, details)

    def error(self, event, message, details=None):
        self._log("ERROR", event, message, details)

    def warning(self, event, message, details=None):
        self._log("WARNING", event, message, details)

# Singleton para facilitar uso global
logger = FloseLogger()
