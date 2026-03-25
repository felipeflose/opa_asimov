import streamlit as st
import os
import time

st.set_page_config(page_title="Flose AI | Setup Logs", page_icon="📑", layout="wide")

st.title("📑 Setup & Infrastructure Logs")
st.markdown("---")

LOG_FILE = "setup.log"

st.subheader("Console de Instalação Real-Time")

# Verificação se o arquivo existe
if not os.path.exists(LOG_FILE):
    st.info("Nenhum log gerado ainda. Inicie o deploy na página Home para ver os eventos aqui.")
else:
    # Interface de Logs Estilo Terminal
    log_placeholder = st.empty()
    
    # Checkbox para auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh Logs", value=True)

    def read_logs():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()

    # Loop de atualização (simples para demo)
    if auto_refresh:
        for _ in range(100): # Roda por um tempo ou até mudar de página
            logs = read_logs()
            log_placeholder.code(logs, language="bash")
            time.sleep(2)
            # st.rerun() # O Streamlit gerencia o loop melhor com empty ou rerun
    else:
        logs = read_logs()
        log_placeholder.code(logs, language="bash")

if st.button("🗑️ Limpar Logs"):
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        st.success("Logs removidos.")
        st.rerun()
