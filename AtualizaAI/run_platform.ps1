try {
    # Revoga todas as contas logadas para garantir um inicio do zero
    & gcloud auth revoke --all --quiet
    # Limpa configuracoes de projetos antigos que podem causar erro de permissao
    & gcloud config unset billing/quota_project --quiet
    & gcloud config unset project --quiet
    Write-Host "Todas as contas e configuracoes antigas foram limpas." -ForegroundColor Green
} catch {
    Write-Host "Nenhuma conta encontrada para deslogar ou GCloud nao instalado." -ForegroundColor Gray
}

Write-Host "Iniciando Setup da Flose AI Platform..." -ForegroundColor Cyan

# 1. Criar VENV se nao existir
if (!(Test-Path ".venv")) {
    Write-Host "Criando ambiente virtual (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
}

# 2. Instalar requisitos
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

# 3. Iniciar Dashboard
Write-Host "Abrindo Portal de Instanciacao (Dashboard)..." -ForegroundColor Green
Write-Host "NOTA: O Telegram Bot roda exclusivamente no GCP via Webhook." -ForegroundColor Yellow
$env:PYTHONPATH = "."
& ".\.venv\Scripts\streamlit.exe" run src/dashboard/Home.py
