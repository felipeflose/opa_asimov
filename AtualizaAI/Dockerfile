# Stage 1: Build Frontend (React)
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Ignorar dependências opcionais para build rápido
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# Stage 2: Python Backend (FastAPI BFF)
FROM python:3.11-slim
WORKDIR /app

# Dependências do sistema mínimas para Cloud Run e Health Check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Instalação de dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cópia do código estruturado V3 + Legado (Src)
COPY api/ ./api/
COPY core/ ./core/
COPY src/ ./src/
COPY agents_v3/ ./agents_v3/
COPY storage_v3/ ./storage_v3/
COPY services/ ./services/
COPY entrypoint.py .

# Copia o build do frontend gerado no Stage 1
# No entrypoint, ele procura em ./frontend/dist
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Configurações de ambiente
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# Comando de inicialização unificado (Telegram + BFF + Frontend)
CMD ["python", "entrypoint.py"]
