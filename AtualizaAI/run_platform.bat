@echo off
echo 🚀 Iniciando Flose AI Platform...

:: 1. Criar VENV se não existir
if not exist .venv (
    echo 📦 Criando ambiente virtual (.venv)...
    python -m venv .venv
)

:: 2. Instalar requisitos
echo 🛠️ Verificando/Instalando dependências...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 3. Rodar Streamlit
echo ✨ Subindo o Command Center...
set PYTHONPATH=%cd%
.venv\Scripts\streamlit.exe run src/dashboard/app.py

pause
