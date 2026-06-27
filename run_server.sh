#!/bin/bash

# Habilita modo de interrupção imediata em caso de erro em comandos sequenciais
set -e

# Diretório base da aplicação (ajustável via FLOSE_APP_DIR)
APP_DIR="${FLOSE_APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"
cd "$APP_DIR"

echo "[INFO] Inicializando a infraestrutura do Flos Cockpit..."

# Verifica se o ambiente virtual existe antes de ativar
if [ ! -d "$APP_DIR/.venv" ]; then
    echo "[CRITICAL] Diretório .venv não localizado em: $APP_DIR" >&2
    echo "Por favor, crie o ambiente virtual executando: python3 -m venv .venv" >&2
    exit 1
fi

if [ ! -f "$APP_DIR/.venv/bin/activate" ]; then
    echo "[CRITICAL] Script de ativação do virtualenv não encontrado." >&2
    exit 1
fi

# Ativa o ambiente virtual do Python
source "$APP_DIR/.venv/bin/activate"

# Valida se as dependências do requirements.txt estão instaladas verificando módulos principais
if ! python3 -c "import flask, psutil, telegram" >/dev/null 2>&1; then
    echo "[WARNING] Módulos fundamentais não localizados no virtualenv."
    echo "Executando instalação automática de dependências (pip install)..."
    pip install -r requirements.txt
fi

# Garante que a pasta de logs existe
mkdir -p logs

echo "[INFO] Iniciando o servidor Flask em http://localhost:${PORT:-8091}"
echo "--- Iniciando servidor em $(date) ---" >> logs/server.log

# O uso de exec substitui o processo do shell pelo do Python, permitindo
# que sinais do SO (como SIGTERM, SIGINT) sejam propagados corretamente para o Flask.
exec python3 app.py
