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

# 3. Iniciar Bot Telegram (Always On - Segundo Plano)
Write-Host "🤖 Iniciando Telegram Bot Bridge (Segundo Plano)..." -ForegroundColor Cyan
Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "run_telegram_bot.py" -WindowStyle Hidden

# 4. Rodar Streamlit
Write-Host "Abrindo Portal de Instanciacao..." -ForegroundColor Green
$env:PYTHONPATH = "."
& ".\.venv\Scripts\streamlit.exe" run src/dashboard/Home.py
