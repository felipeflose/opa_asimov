#!/bin/bash

# ==============================================================================
# Script de Sincronização e Atualização do Grafo de Conhecimento (Pipeline)
# ==============================================================================
# Este script executa duas etapas cruciais de forma sequencial:
#   1. Sincroniza e converte novos arquivos do MBA (como PDFs) para HTML/Markdown
#      utilizando o Docling e BeautifulSoup no script agent_sync_mba.py.
#   2. Atualiza a modelagem de entidades do grafo e reconstrói as conexões semânticas
#      com agent_graph_generator.py utilizando chamadas ao Ollama local.
#
# Configurações:
#   - O log detalhado de execução é gravado e anexado em logs/update_graph.log.
# ==============================================================================

# Define o diretório de execução do projeto
APP_DIR="${FLOSE_APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"
cd "$APP_DIR"

# Ativa o ambiente virtual (.venv) do Python para garantir as dependências corretas
if [ -f "$APP_DIR/.venv/bin/activate" ]; then
    source "$APP_DIR/.venv/bin/activate"
fi

# Cria a pasta de logs locais caso não exista
mkdir -p logs

# Passo 1: Execução do Sincronizador de Disciplinas do MBA (Conversão Docling)
echo "--- [PASSO 1/2] Sincronizando PDFs do MBA: $(date) ---" >> logs/update_graph.log
python3 "$APP_DIR/agent_sync_mba.py" >> logs/update_graph.log 2>&1

# Passo 2: Execução do Pipeline Gerador e Atualizador do Grafo
echo "--- [PASSO 2/2] Iniciando atualização do Grafo: $(date) ---" >> logs/update_graph.log
python3 -u agent_graph_generator.py >> logs/update_graph.log 2>&1
echo "--- [FIM] Sincronização e Atualização concluídas com sucesso: $(date) ---" >> logs/update_graph.log
