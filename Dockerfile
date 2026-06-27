FROM python:3.9-slim

# Define o diretório de trabalho interno
WORKDIR /app

# Instala pacotes do sistema fundamentais para monitoramento e compilações
RUN apt-get update && apt-get install -y --no-install-recommends \
    procps \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos de produção congelados e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código-fonte para o contêiner
COPY . .

# Cria os diretórios necessários
RUN mkdir -p logs backups vault_temp summaries

# Expõe a porta padrão do Flask
EXPOSE 8091

# Variáveis de ambiente default de produção
ENV FLASK_DEBUG=false
ENV PORT=8091
ENV FLOSE_APP_DIR=/app

# Comando de execução padrão (executa o servidor Flask)
# Sinais do Docker (SIGTERM) são passados corretamente utilizando o formato exec (array JSON)
CMD ["python", "app.py"]
