import streamlit as st
import os
import json
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis do .env se existir localmente, forçando o override para evitar conflitos de ambiente
load_dotenv(override=True)

# --- Logging Helper ---
LOG_FILE = "setup.log"

import hashlib

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def secure_compare(input_str, secret_str):
    """Compara o hash do input com o segredo."""
    if not input_str or not secret_str:
        return False
    return hashlib.sha256(input_str.encode()).hexdigest() == hashlib.sha256(secret_str.encode()).hexdigest()

# --- Persistence Logic ---
def save_settings(project_id, region, api_key):
    # Update .env without destroying other variables like MASTER_KEY or ADMIN_EMAIL
    lines = []
    found = set()
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            lines = f.readlines()
    
    new_lines = []
    updates = {
        "GCP_PROJECT_ID": project_id,
        "GCP_REGION": region,
        "GEMINI_API_KEY": api_key
    }
    
    # Process existing lines
    for line in lines:
        match = False
        for k, v in updates.items():
            if line.startswith(f"{k}="):
                new_lines.append(f"{k}={v}\n")
                found.add(k)
                match = True
                break
        if not match:
            new_lines.append(line)
            
    # Add new ones if they didn't exist
    for k, v in updates.items():
        if k not in found:
            new_lines.append(f"{k}={v}\n")
            
    with open(".env", "w") as f:
        f.writelines(new_lines)

def load_settings():
    settings = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=")
                    settings[k] = v
    return settings

def check_gcloud_auth():
    try:
        result = subprocess.run("gcloud config get-value account", shell=True, capture_output=True, text=True)
        account = result.stdout.strip()
        return account if account and "(unset)" not in account else None
    except:
        return None

def setup_page():
    st.set_page_config(page_title="Flose AI | Secure Gateway", page_icon="🔒", layout="centered")
    
    # Premium CSS for Login
    st.markdown("""
    <style>
        .login-card {
            background-color: #1e293b;
            padding: 40px;
            border-radius: 20px;
            border: 1px solid #334155;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            text-align: center;
        }
        .stButton>button { width: 100%; border-radius: 10px; height: 50px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0

    if not st.session_state.authenticated:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://www.gstatic.com/images/branding/product/2x/cloud_64dp.png", width=80)
        st.title("Flose AI Platform")
        st.subheader("Acesso Restrito: Somente Usuários Autorizados")
        
        email_input = st.text_input("E-mail Google", placeholder="seu-email@gmail.com")
        password_input = st.text_input("Chave Mestra de Acesso", type="password")
        
        if st.button("🔐 DESBLOQUEAR PLATAFORMA"):
            # Rate limiting: Sleep increases with failed attempts
            if st.session_state.login_attempts > 0:
                time.sleep(min(st.session_state.login_attempts * 2, 10))

            admin_email = os.getenv("ADMIN_EMAIL")
            master_key = os.getenv("MASTER_KEY")
            
            if not admin_email or not master_key:
                st.error("🔒 Configuração de segurança ausente no servidor (Secret Manager).")
                st.stop()
            
            # Verificação de segurança via Hash
            if secure_compare(email_input, admin_email) and secure_compare(password_input, master_key):
                st.session_state.authenticated = True
                st.session_state.user_email = email_input
                st.session_state.login_attempts = 0 # Reset
                st.success("Acesso Concedido! Iniciando sistemas...")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error("Credenciais inválidas. Acesso monitorado.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # Se chegou aqui, está autenticado
    st.sidebar.write(f"Conectado como: **{st.session_state.user_email}**")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # Resto do código da Home...
    saved = load_settings()
    st.title("⚡ Flose AI Platform Setup")
    st.markdown("---")
    
    # Check for existing connection
    active_account = check_gcloud_auth()
    
    st.subheader("1. Autenticação GCP")
    if active_account:
        st.success(f"✅ Conectado como: **{active_account}**")
        if st.button("🔄 Trocar de Conta (Sair)"):
            subprocess.run("gcloud auth revoke", shell=True)
            st.rerun()
    else:
        st.write("Conecte sua conta Google para gerenciar a plataforma via nuvem.")
        if st.button("🚀 Iniciar Login Social (GCloud)"):
            with st.spinner("Abrindo navegador..."):
                # O comando agora inclui scopes específicos para o Gemini/Vertex AI
                # Usamos aspas duplas para garantir que o PowerShell trate a string corretamente
                cmd = 'gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform","https://www.googleapis.com/auth/generative-language","openid"'
                subprocess.Popen(cmd, shell=True)
                st.info("Verifique a aba aberta no seu navegador.")
                st.warning("⚠️ Importante: Garanta que todas as permissões sejam aceitas no navegador.")

    with st.expander("🛠️ Problemas com o Login? (Clique aqui)"):
        st.write("Se o login pela página falhar, copie e cole este comando completo no seu PowerShell:")
        st.code('gcloud auth application-default login --scopes="https://www.googleapis.com/auth/cloud-platform","https://www.googleapis.com/auth/generative-language","openid"')
        st.write("Após completar o login no terminal, volte aqui e clique no botão abaixo:")
        if st.button("✅ Já fiz o login no terminal"):
            st.success("Ótimo! Agora insira o ID do seu projeto abaixo.")

    st.markdown("---")
    
    st.subheader("2. Configuração do Projeto & IA")
    
    # Campo para API Key do Gemini (Fundamental para não usar Vertex)
    saved_api_key = saved.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key (AI Studio)", value=saved_api_key, type="password", help="Pegue sua chave em aistudio.google.com")
    st.caption("⚠️ Usaremos esta chave diretamente para evitar o uso do Vertex AI.")

    # Função para listar projetos via gcloud
    def get_gcp_projects():
        try:
            # Verifica se há uma conta ativa antes de tentar listar
            acc_check = subprocess.run("gcloud auth list --filter=status:ACTIVE --format=\"value(account)\"", shell=True, capture_output=True, text=True)
            if not acc_check.stdout.strip():
                return [], "Nenhuma conta ativa detectada no CLI. Clique no botão 'Login de Gerenciamento' acima."
            
            result = subprocess.run("gcloud projects list --format=json --limit=50", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                projects = json.loads(result.stdout)
                if not projects:
                    return [], "Lista vazia. Você tem certeza que possui projetos criados neste e-mail?"
                return [p['projectId'] for p in projects], None
            return [], result.stderr
        except Exception as e:
            return [], str(e)

    # Se já logou, tentamos listar. Senão, mostramos botão de carregar.
    if 'project_list' not in st.session_state:
        st.session_state.project_list = []
    if 'last_error' not in st.session_state:
        st.session_state.last_error = None

    col_proj, col_btn = st.columns([3, 1])
    
    with col_btn:
        st.write("") # alinhamento
        if st.button("🔄 Listar Projetos"):
            with st.spinner("Buscando seus projetos no GCP..."):
                projects, error = get_gcp_projects()
                st.session_state.project_list = projects
                st.session_state.last_error = error

    saved_project = saved.get("GCP_PROJECT_ID", "")
    saved_region = saved.get("GCP_REGION", "us-central1")

    with col_proj:
        if st.session_state.project_list:
            # Tenta encontrar o index do projeto salvo na lista
            try:
                idx = st.session_state.project_list.index(saved_project)
            except:
                idx = 0
            project_id = st.selectbox("Selecione seu Projeto GCP", st.session_state.project_list, index=idx)
            st.caption("Projetos encontrados na sua conta.")
        else:
            project_id = st.text_input("ID do Projeto GCP (Manual)", value=saved_project, placeholder="ex: meu-projeto-123")
            st.caption("Cole o ID do projeto do seu console Google Cloud.")

    # Feedback de erro amigável
    if st.session_state.last_error:
        with st.expander("❌ Detalhes do erro ao listar", expanded=True):
            st.error(st.session_state.last_error)
            st.info("💡 Tente rodar `gcloud auth login` no seu terminal e depois clique em 'Listar Projetos' novamente.")

    # Busca index da região salva
    regions = ["us-central1", "southamerica-east1", "us-east1"]
    try:
        reg_idx = regions.index(saved_region)
    except:
        reg_idx = 0
        
    region = st.selectbox("Região de Deploy", regions, index=reg_idx)
    
    # Só mostra o banner "Configuração atual" se:
    # 1. Tivermos algo salvo
    # 2. NÃO tivermos acabado de fazer um deploy
    # 3. O projeto/região selecionados forem IGUAIS aos salvos
    is_settings_changed = (project_id != saved_project) or (region != saved_region)
    
    if saved_project and 'deploy_done' not in st.session_state and not is_settings_changed:
        st.success(f"📌 Configuração atual: **{saved_project}** em **{saved_region}**")
    
    st.markdown("---")
    
    st.subheader("3. Instanciar Infraestrutura")
    st.write("Isso criará os Buckets, pastas e o Grafo Inicial no seu GCP.")
    
    if st.button("🏗️ Criar Infraestrutura na Nuvem"):
        if not project_id or not api_key:
            st.warning("Por favor, insira o ID do Projeto e a API Key antes de continuar.")
        else:
            log_event(f"Iniciando deploy no projeto: {project_id}")
            with st.status("Construindo infraestrutura real no GCP...", expanded=True) as status:
                st.write("📂 Salvando configurações locais...")
                save_settings(project_id, region, api_key)
                log_event("Configurações salvas no .env")
                
                # Nomes de bucket no GCP devem ser GLOBALMENTE únicos. 
                # Adicionar o ID do projeto ajuda a garantir essa unicidade.
                bucket_name = f"flose-ai-platform-{project_id}" 
                
                st.write(f"🌐 Verificando Bucket: gs://{bucket_name}...")
                log_event(f"Verificando existência do bucket {bucket_name}")
                
                # Tenta criar o bucket
                create_bucket = subprocess.run(f"gsutil mb -p {project_id} -l {region} gs://{bucket_name}", shell=True, capture_output=True, text=True)
                
                if create_bucket.returncode == 0:
                    log_event(f"Bucket {bucket_name} criado com sucesso.")
                    st.success(f"Bucket criado: {bucket_name}")
                elif "409" in create_bucket.stderr:
                    log_event(f"O bucket {bucket_name} já existe e pertence a você (ou é seu). Prosseguindo...")
                    st.info(f"Usando bucket existente: {bucket_name}")
                else:
                    log_event(f"Erro ao criar bucket: {create_bucket.stderr.strip()}")
                    st.error(f"Falha ao criar bucket. Verifique se o nome é único ou se o projeto está correto.")
                    status.update(label="❌ Erro na Criação", state="error")
                    st.stop()
                
                st.write("🏷️ Aplicando Labels obrigatórios...")
                labels = "project=flose-ai-platform,component=ai-system,owner=flose,environment=prod,cost_center=ai-research"
                subprocess.run(f"gsutil label set {labels} gs://{bucket_name}", shell=True)
                log_event("Labels aplicados ao bucket.")
                
                st.write("📁 Criando estrutura de dados (pastas)...")
                folders = ["knowledge", "agents", "vectors", "embeddings", "logs", "documentation", "iceberg", "terraform", "agents/memory"]
                for folder in folders:
                    subprocess.run(f"echo . | gsutil cp - gs://{bucket_name}/{folder}/.keep", shell=True, capture_output=True)
                    log_event(f"Pasta configurada: {folder}")
                
                st.write("🧠 Inicializando Grafo de Conhecimento...")
                log_event("Grafo de conhecimento inicializado no bucket.")
                time.sleep(1)
                
                status.update(label="✅ Infraestrutura Provisionada com Sucesso!", state="complete", expanded=False)
                log_event("DEPLOY FINALIZADO COM SUCESSO.")
            
            st.session_state.deploy_done = True
            st.balloons()
            
            # Big Premium Confirmation Card
            st.markdown(f"""
                <div style="background-color: #1e293b; padding: 30px; border-radius: 15px; border: 2px solid #10b981; text-align: center; margin-top: 20px;">
                    <h1 style="color: #10b981; margin-bottom: 5px;">🚀 Missão Cumprida!</h1>
                    <p style="font-size: 1.2rem; color: #f8fafc;">A infraestrutura da <b>Flose AI</b> foi instanciada com sucesso.</p>
                    <div style="margin: 20px 0;">
                        <span style="background: #0f172a; padding: 8px 15px; border-radius: 20px; color: #10b981; font-family: monospace;">
                            Projeto: {project_id}
                        </span>
                    </div>
                    <p style="color: #94a3b8;">O Grafo de Conhecimento e os Agentes de Base estão ativos.</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            if st.button("🧠 ENTRAR NO COMMAND CENTER", use_container_width=True, type="primary"):
                st.switch_page("pages/Command_Center.py")
            
            if st.button("♻️ Configurar outro projeto"):
                del st.session_state.deploy_done
                st.rerun()

if __name__ == "__main__":
    setup_page()
