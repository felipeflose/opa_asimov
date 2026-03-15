# Usar Python como base
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO o projeto (incluindo a pasta frontend/dist gerada localmente)
COPY . .

# Variáveis de Ambiente
ENV PORT=8080
ENV PYTHONUNBUFFERED=True

EXPOSE 8080

CMD ["python", "entrypoint.py"]
