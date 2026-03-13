import streamlit as st
import pandas as pd
import json
import os
import sys
import time
import subprocess
import networkx as nx
import psutil
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Ensure the project root is in PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import Platform Core
from src.orchestrator.cognitive_orchestrator import CognitiveOrchestrator
from src.storage.gcs_client import GCSClient
from src.graph.knowledge_graph import KnowledgeGraphManager
from src.storage.finops_manager import FinOpsManager
from src.storage.gcp_resource_manager import GCPResourceManager

# Load Environment
load_dotenv()

# Premium Page Config
st.set_page_config(
    page_title="Flose AI Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Auth Guard ---
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Acesso restrito. Por favor, faça login na página inicial.")
    if st.button("Voltar para Home"):
        st.switch_page("Home.py")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; background-color: #1e2130; margin-bottom: 10px; border: 1px solid #3e4150; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4150; }
</style>
""", unsafe_allow_html=True)

# --- Initial Setup ---
if 'orchestrator' not in st.session_state:
    project_id = os.getenv("GCP_PROJECT_ID")
    bucket_name = f"flose-ai-platform-{project_id}"
    
    # GCSClient (v3 Fix): Explicit Project Pass
    # Passamos o project_id explicitamente para não depender do ambiente (evita OSError)
    gcs = GCSClient(bucket_name, project_id=project_id) 
    api_key = os.getenv("GEMINI_API_KEY")
    
    st.session_state.gcs = gcs
    st.session_state.finops = FinOpsManager(gcs_client=gcs)
    st.session_state.gcp = GCPResourceManager(project_id=project_id)
    st.session_state.orchestrator = CognitiveOrchestrator(api_key=api_key, gcs_client=gcs, finops_manager=st.session_state.finops)
    st.session_state.kg = KnowledgeGraphManager(gcs_client=gcs)
    st.session_state.session_id = f"session_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Tenta carregar histórico se a sessão já existir (previne perda no F5)
    history_file = f"logs/chats/{st.session_state.session_id}.json"
    existing_chat = gcs.read_json(history_file)
    st.session_state.messages = existing_chat.get("messages", []) if existing_chat else []

# Helper to check if bot is running
def is_bot_running():
    try:
        for proc in psutil.process_iter(['cmdline']):
            cmdline = proc.info.get('cmdline')
            if cmdline and any('run_telegram_bot.py' in s for s in cmdline):
                return True
    except:
        pass
    return False

# Helper to save chat to GCS
def save_chat_to_gcs():
    if hasattr(st.session_state, 'gcs') and st.session_state.messages:
        filename = f"logs/chats/{st.session_state.session_id}.json"
        try:
            st.session_state.gcs.upload_json({"messages": st.session_state.messages}, filename)
        except:
            pass

# --- Sidebar ---
st.sidebar.title("🛠️ Control Panel")
st.sidebar.success("System: ONLINE")
gcp_project = st.sidebar.text_input("GCP Project", os.getenv("GCP_PROJECT_ID", "flose-ai-platform"))
bucket_name = st.sidebar.text_input("GCS Bucket", os.getenv("GCS_BUCKET_NAME", "flose-ai-platform"))

if st.sidebar.button("♻️ Reset Session"):
    st.session_state.messages = []
    st.rerun()

# --- Main Dashboard ---
st.title("🧠 Flose AI Platform | Command Center")

tabs = st.tabs(["💬 Chat", "🕵️ Reasoning", "🧠 Memory", "💎 FinOps", "☁️ GCP Infra", "🤖 Agent Library", "🧬 Knowledge Graph", "📝 TRDs", "⚙️ Systems"])

with tabs[0]:
    st.header("Global Orchestrator Chat")
    st.caption("Fale com o Cognitive Orchestrator em PT-BR. Todas as sessões são salvas no seu Bucket.")
    
    # Session Info
    st.sidebar.info(f"Sessão Ativa: {st.session_state.session_id.split('_')[-1]}")
    
    # Chat History Display
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ex: 'Crie um agente de análise de mercado' ou 'Resuma os logs de hoje'"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Suporte para upload de imagem no chat
        uploaded_file = st.sidebar.file_uploader("🖼️ Anexar Imagem ao Comando", type=['png', 'jpg', 'jpeg'])
        temp_img_path = None
        if uploaded_file:
            temp_img_path = f"temp_st_{uploaded_file.name}"
            with open(temp_img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.image(uploaded_file, caption="Imagem anexada", use_container_width=True)

        with st.chat_message("assistant"):
            with st.spinner("Analisando..."):
                # Call Orchestrator com histórico para manter contexto
                decision = st.session_state.orchestrator.process_command(
                    prompt, 
                    image_path=temp_img_path,
                    chat_history=st.session_state.messages
                )
                reasoning = st.session_state.last_reasoning = decision.get("reasoning", "Processando...")
                
                # Executa a decisão para obter o resultado final (mensagens tratadas)
                response_to_user = st.session_state.orchestrator.execute_decision(decision)
                
                # Exibe Reasoning Chain estilizado
                with st.expander("🧠 Ver AI Reasoning Chain", expanded=False):
                    st.info(reasoning)
                
                st.markdown(response_to_user)
                
                # Update KG
                agent_name = decision.get("agent_involved") or "Orchestrator"
                st.session_state.kg.add_interaction(
                    agent_name=agent_name,
                    task_name=f"Command",
                    outcome={
                        "status": "executed", 
                        "learned_concepts": decision.get("knowledge_graph_update", [])
                    }
                )
                
                st.session_state.messages.append({"role": "assistant", "content": response_to_user})
                
                if temp_img_path and os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                
                save_chat_to_gcs()
                st.rerun()

with tabs[1]:
    st.header("🕵️ AI Reasoning Chain")
    if hasattr(st.session_state, 'last_reasoning'):
        st.info(st.session_state.last_reasoning)
    else:
        st.info("Nenhum pensamento processado nesta sessão.")

with tabs[2]:
    st.header("🧠 Persistent Memory (Embeddings)")
    st.caption("Visualização tridimensional (projetada em 2D) da memória semântica da IA.")
    
    vs = st.session_state.orchestrator.vector_store
    
    col_mem1, col_mem2 = st.columns([2, 1])
    
    with col_mem1:
        df_proj = vs.get_projections()
        if df_proj is not None:
            fig_mem = px.scatter(
                df_proj, x='x', y='y', 
                color='type', hover_data=['text', 'source'],
                title="Mapa de Memória Semântica (Embedding Space)",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_mem.update_traces(marker=dict(size=12, opacity=0.8, line=dict(width=1, color='White')))
            st.plotly_chart(fig_mem, use_container_width=True)
        else:
            st.info("A IA ainda não possui memórias suficientes para gerar o mapa de embeddings. Continue conversando!")

    with col_mem2:
        st.subheader("Últimas Entradas")
        if not vs.metadata.empty:
            for _, row in vs.metadata.tail(5).iterrows():
                with st.expander(f"📍 {row['source']} ({row['type']})"):
                    st.write(row['text'])
        else:
            st.write("Memória vazia.")
            
    st.markdown("---")
    st.subheader("🔍 Recuperação de Contexto")
    query_test = st.text_input("Teste de Busca Semântica", placeholder="O que a IA lembra sobre...")
    if query_test:
        results = vs.search(query_test, top_k=3)
        if results:
            for res in results:
                st.write(f"✅ **Distância: {res['distance']:.4f}**")
                st.code(res['text'])
        else:
            st.warning("Nenhum contexto similar encontrado.")

with tabs[3]:
    st.header("💎 FinOps Monitoring")
    
    # Real data from GCS
    summary = st.session_state.finops.get_daily_summary()
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    today_stats = summary.get(today, {"tokens": 0, "cost": 0.0, "calls": 0})
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily Tokens", f"{today_stats['tokens'] / 1000:.1f}k", help="Milhares de tokens hoje")
    c2.metric("Projected Cost", f"${today_stats['cost']:.4f}", help="Custo em USD baseado no Gemini 2.5 Flash")
    c3.metric("API Calls", f"{today_stats['calls']}", help="Número de comandos processados")
    
    # Cost History Chart
    if summary:
        df_fin = pd.DataFrame.from_dict(summary, orient='index').reset_index()
        df_fin.columns = ['Date', 'Tokens', 'Cost', 'Calls']
        st.plotly_chart(px.line(df_fin, x="Date", y="Cost", template="plotly_dark", title="Histórico de Custos (USD)"), use_container_width=True)
    else:
        st.info("Nenhum dado de custo registrado ainda.")

with tabs[4]:
    st.header("☁️ GCP Infrastructure Health")
    st.caption("Monitoramento em tempo real dos recursos ativos no Google Cloud Platform.")
    
    status = st.session_state.gcp.get_cloud_run_status()
    
    if "error" not in status:
        c1, c2, c3 = st.columns(3)
        c1.metric("Service Status", "ACTIVE", delta="Normal", delta_color="normal")
        c2.metric("Region", status["region"])
        c3.metric("Revision", status["revisions"])
        
        st.markdown(f"**URL Pública:** [{status['url']}]({status['url']})")
        st.markdown(f"**Último Deploy:** `{status['last_update']}`")
        
        # Extrato de Consumo
        st.subheader("📊 Extrato de Infraestrutura")
        metrics = st.session_state.gcp.get_usage_metrics()
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.info(f"**CPU utilization:** {metrics['cpu_utilization']}")
            st.info(f"**Memory allocated:** {metrics['memory_usage']}")
        with col_m2:
            st.info(f"**Active Instances:** {metrics['active_instances']}")
            st.info(f"**Buckets GCS:** {', '.join(st.session_state.gcp.list_active_buckets())}")
            
        # Visualização de Alocação
        df_infra = pd.DataFrame({
            "Recurso": ["CPU", "Memory", "Storage", "Network"],
            "Uso": [15, 45, 10, 5] # Simulação de % de cota
        })
        st.plotly_chart(px.bar(df_infra, x="Recurso", y="Uso", title="Alocação de Recursos (%)", template="plotly_dark"), use_container_width=True)
    else:
        st.error(f"Erro ao conectar com GCP APIs: {status['error']}")
        st.info("Certifique-se de que a conta de serviço tem permissões de 'Cloud Run Viewer' e as APIs estão habilitadas.")
with tabs[5]:
    st.header("🤖 Agent Library")
    st.caption("Gerencie seus agentes especializados, edite seus prompts e personalize sua identidade visual.")
    
    # Importação local para evitar circular dependecy se houver
    from src.agents.base_agent import BaseAgent

    registry = st.session_state.gcs.read_json("agents/registry.json")
    
    if registry and "agents" in registry:
        agents_data = registry["agents"]
        
        # Grid de Agentes
        for i, agent in enumerate(agents_data):
            with st.expander(f"🤖 {agent.get('agent_name', 'Agente')} - {agent.get('purpose', 'Sem propósito')}", expanded=(i==0)):
                col_a1, col_a2 = st.columns([1, 3])
                
                with col_a1:
                    avatar_url = agent.get('avatar', "https://api.dicebear.com/7.x/bottts/svg?seed=" + agent.get('agent_name', 'bot'))
                    st.image(avatar_url, width=100)
                    new_avatar = st.text_input("URL da Foto", value=avatar_url, key=f"avatar_{agent['agent_name']}")
                
                with col_a2:
                    agent_name = agent.get('agent_name')
                    purpose = st.text_input("Propósito", value=agent.get('purpose', ''), key=f"purpose_{agent_name}")
                    
                    system_prompt = st.text_area(
                        "System Prompt (Personalidade e Regras)", 
                        value=agent.get('system_prompt', f"Você é o {agent_name}."), 
                        height=150,
                        key=f"prompt_{agent_name}"
                    )
                    
                    if st.button(f"💾 Salvar Alterações: {agent_name}", key=f"save_{agent_name}"):
                        # Criar instância e salvar de volta no GCS
                        obj = BaseAgent(
                            name=agent_name,
                            purpose=purpose,
                            system_prompt=system_prompt,
                            avatar=new_avatar,
                            tools=agent.get('tools', []),
                            gcs_client=st.session_state.gcs
                        )
                        obj.save_to_registry()
                        st.success(f"Configurações de {agent_name} atualizadas!")
                        st.rerun()
                
                st.info(f"📅 Criado em: {agent.get('created_at', 'Desconhecido')}")
    else:
        st.info("Nenhum agente customizado encontrado. O Orchestrator criará novos conforme necessário!")
        # Mostrar agentes core apenas como referência
        core_agents = [
            {"Name": "CognitiveOrchestrator", "Avatar": "🧠", "Role": "Master Controller"},
            {"Name": "FinOpsGuardian", "Avatar": "🛡️", "Role": "Cost Monitor"},
            {"Name": "VisionAgent", "Avatar": "👁️", "Role": "Visual Analysis"}
        ]
        st.write("### 🏗️ Core Platform Agents (Read-only)")
        for agent in core_agents:
            st.write(f"- {agent['Avatar']} **{agent['Name']}**: {agent['Role']}")

with tabs[6]:
    col_kg1, col_kg2 = st.columns([4, 1])
    with col_kg1:
        st.header("🧬 Interactive Knowledge Graph")
    with col_kg2:
        if st.button("🔄 Sync Cloud", help="Sincronizar grafo com o Telegram/GCS"):
            st.session_state.kg.load()
            st.rerun()
            
    st.caption("Veja o que a IA está aprendendo em tempo real. O grafo é sincronizado automaticamente entre o Telegram e este painel.")
    
    # Auto-load on view
    st.session_state.kg.load()
    graph = st.session_state.kg.graph
    if len(graph.nodes()) > 0:
        # --- D3.js Premium Interactive Graph ---
        nodes = []
        links = []
        
        # Filtro de renderização: esconde lixo que persistiu ou escapou
        valid_nodes = [n for n in graph.nodes() if not str(n).startswith("Interação") and not str(n).startswith("Command")]
        
        for node in valid_nodes:
            ntype = graph.nodes[node].get('type', 'unknown')
            
            # Paleta de Cores Premium (Flose = Gold, Pilares = Blue, Conceitos = Cyan/Green)
            color = "#4b6cb7" # Azul padrão (Pillars)
            size = 18
            
            if node == "Flose": 
                color = "#ffd700" # GOLD
                size = 28
            elif ntype == "pilar":
                color = "#3b82f6" # Vibrant Blue
                size = 22
            elif ntype == "concept": 
                color = "#10b981" # Greenish Concept
                size = 12
            elif ntype == "mvp":
                color = "#8b5cf6" # purple
                size = 18
                
            nodes.append({"id": node, "group": ntype, "color": color, "size": size})
            
        for edge in graph.edges(data=True):
            if edge[0] in valid_nodes and edge[1] in valid_nodes:
                links.append({"source": edge[0], "target": edge[1], "value": 1})

        # Template HTML/JS para o D3.js
        # Escapando chaves {{ }} para f-strings não quebrarem o JS
        d3_html = f"""
        <div id="graph-container" style="width: 100%; height: 600px; background: #0e1117; border-radius: 15px; border: 1px solid #3e4150;"></div>
        <script src="https://d3js.org/d3.v6.min.js"></script>
        <script>
            const data = {{
                nodes: {json.dumps(nodes)},
                links: {json.dumps(links)}
            }};

            const width = document.getElementById('graph-container').clientWidth;
            const height = 600;

            const svg = d3.select("#graph-container")
                .append("svg")
                .attr("width", "100%")
                .attr("height", height)
                .call(d3.zoom().on("zoom", (event) => {{
                    container.attr("transform", event.transform);
                }}))
                .append("g");

            const container = svg.append("g");

            const simulation = d3.forceSimulation(data.nodes)
                .force("link", d3.forceLink(data.links).id(d => d.id).distance(120))
                .force("charge", d3.forceManyBody().strength(-400))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(40));

            const link = container.append("g")
                .attr("stroke", "#555")
                .attr("stroke-opacity", 0.4)
                .selectAll("line")
                .data(data.links)
                .join("line")
                .attr("stroke-width", 1.5);

            const node = container.append("g")
                .selectAll("g")
                .data(data.nodes)
                .join("g")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            node.append("circle")
                .attr("r", d => d.size)
                .attr("fill", d => d.color)
                .attr("stroke", "#fff")
                .attr("stroke-width", 2)
                .style("cursor", "pointer")
                .style("filter", d => `drop-shadow(0 0 8px ${{d.color}}99)`);

            node.append("text")
                .text(d => d.id)
                .attr("x", 0)
                .attr("y", d => d.size + 18)
                .attr("text-anchor", "middle")
                .attr("fill", "#e0e0e0")
                .style("font-size", "13px")
                .style("font-weight", "500")
                .style("font-family", "'Inter', sans-serif")
                .style("pointer-events", "none");

            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});

            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}

            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}

            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                // Para manter a posição fixa após o drag, não mude fx/fy para null
            }}
        </script>
        """
        components.html(d3_html, height=620)
    else:
        st.info("Ainda não há dados no Grafo. Comece a conversar com a IA para ver a mágica acontecer!")

with tabs[7]:
    st.header("📋 TRD Kanban Board")
    st.caption("Acompanhamento visual das demandas (Tasks, Reports & Deliverables).")
    
    demands_data = st.session_state.gcs.read_json("demands/registry.json")
    if demands_data and "demands" in demands_data:
        df_demands = pd.DataFrame(demands_data["demands"])
        
        # Dashboard Stats
        c1, c2, c3 = st.columns(3)
        total = len(df_demands)
        pending = len(df_demands[df_demands['status'] == 'Aberto'])
        done = len(df_demands[df_demands['status'] == 'Concluído'])
        
        c1.metric("Total de Demandas", total)
        c2.metric("Pendentes", pending, delta=f"{pending} tasks", delta_color="inverse")
        c3.metric("Concluídas", done, delta=f"{done} tasks")

        st.markdown("---")
        
        # Kanban Columns
        cols = st.columns(3)
        states = ["Aberto", "Em Progresso", "Concluído"]
        colors = ["#ff4b4b", "#0083B0", "#28a745"]
        icons = ["🔴", "🔵", "🟢"]
        
        for i, state in enumerate(states):
            with cols[i]:
                st.markdown(f"### {icons[i]} {state}")
                state_tasks = df_demands[df_demands['status'] == state]
                
                if state_tasks.empty:
                    st.info(f"Sem itens em {state}")
                else:
                    for _, task in state_tasks.iterrows():
                        # --- Governance & Approval Info ---
                        budget_ok = task.get('budget_approved', False)
                        has_tf = bool(task.get('terraform_plan'))
                        priority_color = "#f9ed69" if task['priority'] == 'Alta' else "#e0e0e0"
                        
                        with st.container():
                            st.markdown(f"""
<div style="background-color: #1e1e1e; border-left: 5px solid {colors[i]}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-right: 1px solid #333; border-top: 1px solid #333; border-bottom: 1px solid #333;">
<div style="display: flex; justify-content: space-between;">
<h4 style="margin: 0; color: #fff;">{task['title']}</h4>
<span>{'✅' if budget_ok else '⏳'}</span>
</div>
<p style="font-size: 12px; color: #aaa; margin: 5px 0;">ID: <code>{task['id']}</code></p>
{f'<div style="font-size: 11px; color: #4dabf7; margin-top: 5px;">🏗️ Terraform Ready</div>' if has_tf else ''}
<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
<span style="background-color: {priority_color}; color: #333; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{task['priority']}</span>
<span style="color: #888; font-size: 11px;">👤 {task['responsible']}</span>
</div>
</div>
""", unsafe_allow_html=True)
                            
                            # Interações de Governança
                            if state == "Aberto":
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    if st.button("📄 Ver Specs", key=f"spec_{task['id']}"):
                                        st.info(f"**Custo/Explicação:** {task.get('cost_explanation', 'Aguardando Análise...')}")
                                        if has_tf: 
                                            st.code(task.get('terraform_plan'), language="hcl")
                                with col_btn2:
                                    if not budget_ok:
                                        if st.button("👍 Dar OK", key=f"ok_{task['id']}", type="primary"):
                                            # Atualiza no GCS
                                            for idx, d in enumerate(demands_data['demands']):
                                                if d['id'] == task['id']:
                                                    demands_data['demands'][idx]['budget_approved'] = True
                                                    break
                                            st.session_state.gcs.upload_json(demands_data, "demands/registry.json")
                                            st.success("Aprovado!")
                                            time.sleep(1)
                                            st.rerun()
                                    else:
                                        st.write("✅ **Aprovado**")
                            
                            elif state == "Concluído":
                                if st.button("🎁 Ver Entrega", key=f"res_{task['id']}", use_container_width=True):
                                    res_id = task.get('result_id')
                                    if res_id:
                                        with st.expander("📦 Resultado da Execução", expanded=True):
                                            res_data = st.session_state.gcs.read_json(f"logs/executions/{res_id}.json")
                                            if res_data:
                                                st.markdown(f"**Agente:** `{res_data.get('agent')}`")
                                                st.markdown(f"**Data:** {res_data.get('timestamp')}")
                                                st.divider()
                                                st.markdown(res_data.get('result'))
                                            else:
                                                st.error("Log de execução não encontrado.")
                                    else:
                                        st.warning("Nenhum ID de resultado vinculado.")
                            
        st.markdown("---")
        
        # --- 🧬 AGENT TASK RUNNER ---
        st.subheader("🧬 Agent Task Runner")
        st.caption("Selecione uma demanda aberta para que um agente especializado a execute.")
        
        open_tasks = df_demands[df_demands['status'] == 'Aberto']
        
        if not open_tasks.empty:
            col_tr1, col_tr2, col_tr3 = st.columns([2, 1, 1])
            
            with col_tr1:
                selected_task_title = st.selectbox("Selecione a Tarefa", open_tasks['title'].tolist())
                selected_task = open_tasks[open_tasks['title'] == selected_task_title].iloc[0]
            
            with col_tr2:
                # Carrega agentes disponíveis
                reg = st.session_state.gcs.read_json("agents/registry.json") or {"agents": []}
                agent_names = [a['agent_name'] for a in reg['agents']]
                selected_agent_name = st.selectbox("Delegar para Agente", agent_names)
            
            with col_tr3:
                st.write("") # ajuste
                # Trava de Segurança: Só executa se aprovado
                can_execute = selected_task.get('budget_approved', False)
                
                if st.button("🚀 EXECUTAR TAREFA", type="primary", use_container_width=True, disabled=not can_execute):
                    with st.spinner(f"O agente {selected_agent_name} está trabalhando..."):
                        # Busca os dados do agente
                        agent_data = next((a for a in reg['agents'] if a['agent_name'] == selected_agent_name), None)
                        if agent_data:
                            # Instancia e Executa
                            agent_obj = BaseAgent(
                                name=agent_data['agent_name'],
                                purpose=agent_data['purpose'],
                                system_prompt=agent_data['system_prompt'],
                                gcs_client=st.session_state.gcs
                            )
                            result = agent_obj.run(f"Tarefa: {selected_task['title']}\nPrioridade: {selected_task['priority']}\nContexto: {selected_task.get('description', 'N/A')}")
                            
                            # Salva o resultado
                            execution_id = f"EX_{os.urandom(4).hex()}"
                            exec_data = {
                                "task_id": selected_task['id'],
                                "agent": selected_agent_name,
                                "result": result,
                                "timestamp": pd.Timestamp.now().isoformat()
                            }
                            st.session_state.gcs.upload_json(exec_data, f"logs/executions/{execution_id}.json")
                            
                            # Atualiza status no registry de demandas
                            for i, d in enumerate(demands_data['demands']):
                                if d['id'] == selected_task['id']:
                                    demands_data['demands'][i]['status'] = 'Concluído'
                                    demands_data['demands'][i]['result_id'] = execution_id
                                    break
                            st.session_state.gcs.upload_json(demands_data, "demands/registry.json")
                            
                            st.success(f"Tarefa concluída por {selected_agent_name}!")
                            st.info(f"**Resultado:**\n{result}")
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
        else:
            st.info("Não há tarefas abertas no backlog para execução automática.")

        if st.checkbox("Ver Tabela Bruta (Raw Data)"):
            st.dataframe(df_demands, use_container_width=True)
    else:
        st.info("Nenhuma demanda registrada no sistema até o momento.")

with tabs[8]:
    st.header("⚙️ Systems Intelligence")
    st.caption("Controle central de serviços e integração de bot.")
    
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t2:
        st.subheader("Controle do Bot")
        bot_on = is_bot_running()
        
        if bot_on:
            st.success("🤖 Bot está ATIVO")
            if st.button("♻️ Reiniciar Bot"):
                for proc in psutil.process_iter(['cmdline']):
                    cmdline = proc.info.get('cmdline')
                    if cmdline and any('run_telegram_bot.py' in s for s in cmdline):
                        proc.kill()
                subprocess.Popen([sys.executable, "run_telegram_bot.py"], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                st.rerun()
        else:
            st.error("🛑 Bot está OFFLINE")
            if st.button("🚀 Iniciar Bot Telegram"):
                try:
                    subprocess.Popen([sys.executable, "run_telegram_bot.py"], 
                                     creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
                    st.success("Bot iniciado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao iniciar bot: {e}")
        
        st.metric("Status do Processo", "ATIVO" if bot_on else "OFFLINE")

    with col_t1:
        st.subheader("Console de Logs Telegram")
        LOG_FILE_TG = "telegram_bot.log"
        if os.path.exists(LOG_FILE_TG):
            with open(LOG_FILE_TG, "r", encoding="utf-8") as f:
                logs_tg = f.readlines()
            st.code("".join(logs_tg[-15:]), language="bash")
        else:
            st.info("Aguardando logs...")
