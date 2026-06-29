// ============================================================
// ESTADO DA APLICAÇÃO
// ============================================================
let activeLogFilter = 'all';
let allSummaries = [];
let studySearchTerm = '';
let studyCurrentPage = 1;
const studyPageSize = 6;

// Histórico circular de sparklines (últimas 18 amostras)
const sparkHistory = { cpu: [], ram: [] };
const SPARK_MAX = 18;

// Mapeamento das posições dos ícones da sidebar (para a pílula)
const NAV_ORDER = ['home', 'graph', 'bot', 'system', 'study', 'rinha', 'kanban', 'office'];

// ============================================================
// UTILITÁRIOS
// ============================================================

function apiHeaders() {
    const h = { 'Content-Type': 'application/json' };
    const savedKey = localStorage.getItem('FLOSE_API_KEY');
    if (savedKey) h['X-API-Key'] = savedKey;
    return h;
}

// Anima contagem de número: start → end em `duration` ms
function animateValue(el, start, end, duration = 900) {
    if (!el) return;
    const range = end - start;
    if (range === 0) { el.textContent = end; return; }
    const startTime = performance.now();
    const step = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Easing easeOutExpo
        const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const current = Math.round(start + range * eased);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

// Renderiza sparkline a partir do histórico
function renderSparkline(containerId, history, isAccent = false) {
    const container = document.getElementById(containerId);
    if (!container || history.length === 0) return;
    const max = Math.max(...history, 1);
    container.innerHTML = history.map((v, i) => {
        const heightPct = Math.max(8, Math.round((v / max) * 100));
        const isLast = i === history.length - 1;
        const accentClass = isAccent ? 'accent-bar' : '';
        return `<div class="sparkline-bar ${accentClass}" style="height: ${heightPct}%;"></div>`;
    }).join('');
}

// Ripple effect em qualquer elemento
function createRipple(element, e) {
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = (e.clientX - rect.left) - size / 2;
    const y = (e.clientY - rect.top) - size / 2;
    const ripple = document.createElement('span');
    ripple.className = 'ripple-wave';
    ripple.style.cssText = `width:${size}px;height:${size}px;left:${x}px;top:${y}px;`;
    element.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
}

// ============================================================
// API CALL COM LOADING
// ============================================================
async function apiCall(url, method = 'POST', body = null, buttonElement = null) {
    let originalHtml = '';
    if (buttonElement) {
        originalHtml = buttonElement.innerHTML;
        buttonElement.disabled = true;
        buttonElement.innerHTML = `<span class="spinner"></span> Processando...`;
    }
    try {
        let opts = { method, headers: apiHeaders() };
        if (body) opts.body = JSON.stringify(body);
        let r = await fetch(url, opts);
        if (r.status === 401) {
            const newKey = prompt('Autenticação necessária. Digite sua FLOSE_API_KEY:');
            if (newKey) {
                localStorage.setItem('FLOSE_API_KEY', newKey);
                opts.headers = apiHeaders();
                r = await fetch(url, opts);
            } else {
                showToast('Ação não autorizada. Chave de API ausente.', 'error');
                if (buttonElement) { buttonElement.disabled = false; buttonElement.innerHTML = originalHtml; }
                return;
            }
        }
        const d = await r.json();
        if (r.ok) showToast(d.msg || d.message || 'Operação realizada com sucesso!', 'success');
        else showToast(d.msg || d.error || `Erro ${r.status}`, 'error');
        if (buttonElement) { buttonElement.disabled = false; buttonElement.innerHTML = originalHtml; }
        return d;
    } catch (e) {
        showToast('Erro de conexão: ' + e.message, 'error');
        if (buttonElement) { buttonElement.disabled = false; buttonElement.innerHTML = originalHtml; }
    }
}

// ============================================================
// TOASTS
// ============================================================
function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;

    const iconMap = {
        success: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
        error:   `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`,
        info:    `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`
    };
    toast.innerHTML = `${iconMap[type] || ''}<span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-12px)';
        setTimeout(() => toast.remove(), 400);
    }, 3600);
}

// ============================================================
// NAVEGAÇÃO — com pílula deslizante
// ============================================================
function updateNavPill(activePageId) {
    const pill = document.getElementById('nav-pill');
    if (!pill) return;
    const idx = NAV_ORDER.indexOf(activePageId);
    if (idx === -1) return;
    // Cada item .nav-item tem 50px de altura + 20px de margin-bottom = 70px de step
    // A pílula começa em padding-top: 30px
    const ITEM_HEIGHT = 50;
    const ITEM_GAP = 20;
    const PADDING_TOP = 30;
    const top = PADDING_TOP + idx * (ITEM_HEIGHT + ITEM_GAP);
    pill.style.top = top + 'px';
}

let officeInterval = null;

function showPage(pageId, element = null) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + pageId).classList.add('active');
    if (element) {
        element.classList.add('active');
    } else {
        const items = document.querySelectorAll('.nav-item');
        const idx = NAV_ORDER.indexOf(pageId);
        if (idx !== -1 && items[idx]) items[idx].classList.add('active');
    }
    updateNavPill(pageId);
    if (pageId === 'graph') setTimeout(initGraph, 100);
    if (pageId === 'study') loadSummariesData();
    if (pageId === 'rinha') setTimeout(initRinha, 100);
    if (pageId === 'kanban') loadKanban();
    
    // Configura polling do Escritório Virtual apenas quando ativo
    if (pageId === 'office') {
        loadOfficeData();
        if (!officeInterval) {
            officeInterval = setInterval(loadOfficeData, 10000);
        }
    } else {
        if (officeInterval) {
            clearInterval(officeInterval);
            officeInterval = null;
        }
    }
}

// ============================================================
// MODAL COM PARALLAX
// ============================================================
function confirmAction(title, message, onConfirm) {
    const overlay = document.getElementById('modal-overlay');
    const mainContainer = document.getElementById('main-container');

    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').textContent = message;

    const confirmBtn = document.getElementById('modal-confirm-btn');
    const cancelBtn  = document.getElementById('modal-cancel-btn');

    const open = () => {
        overlay.classList.add('open');
        mainContainer.classList.add('modal-dimmed');
    };
    const close = () => {
        overlay.classList.remove('open');
        mainContainer.classList.remove('modal-dimmed');
    };

    confirmBtn.onclick = () => { close(); onConfirm(); };
    cancelBtn.onclick  = close;
    overlay.onclick = (e) => { if (e.target === overlay) close(); };

    open();
}

function handleKillAll(btnElement) {
    confirmAction(
        'Encerrar Todos os Agentes?',
        'Esta ação interrompe imediatamente todos os subprocessos operacionais em execução, incluindo o bot do Telegram e os agentes curadores. Deseja prosseguir?',
        () => { apiCall('/api/kill-all', 'POST', null, btnElement); }
    );
}

// ============================================================
// TELEMETRIA — com count-up, sparklines e flash de console
// ============================================================
let prevTelemetry = { cpu: 0, ram: 0, index: 0 };

async function updateTelemetry() {
    try {
        const r = await fetch('/api/status');
        const d = await r.json();

        // --- CPU ---
        const cpuEl = document.getElementById('stat-cpu');
        const cpuVal = parseFloat(d.telemetry.cpu) || 0;
        animateValue(cpuEl, prevTelemetry.cpu, cpuVal, 800);
        prevTelemetry.cpu = cpuVal;
        document.getElementById('bar-cpu').style.width = cpuVal + '%';
        sparkHistory.cpu.push(cpuVal);
        if (sparkHistory.cpu.length > SPARK_MAX) sparkHistory.cpu.shift();
        renderSparkline('spark-cpu', sparkHistory.cpu, false);

        // --- RAM ---
        const ramEl = document.getElementById('stat-ram');
        const ramVal = parseFloat(d.telemetry.ram_used) || 0;
        if (ramEl) ramEl.textContent = ramVal.toFixed(1);
        document.getElementById('bar-ram').style.width = (d.telemetry.ram_percent || 0) + '%';
        sparkHistory.ram.push(parseFloat(d.telemetry.ram_percent) || 0);
        if (sparkHistory.ram.length > SPARK_MAX) sparkHistory.ram.shift();
        renderSparkline('spark-ram', sparkHistory.ram, true);

        // --- Modelo e RAM Total ---
        const modelEl = document.getElementById('stat-model');
        if (modelEl) modelEl.textContent = d.telemetry.model || '...';
        const ramTotalEl = document.getElementById('stat-ram-total');
        if (ramTotalEl) ramTotalEl.textContent = d.telemetry.ram_total || '0';

        // --- Tags de Status dos Agentes ---
        const updateTag = (id, active) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.textContent = active ? 'ONLINE' : 'IDLE';
            el.className = 'bot-status-tag ' + (active ? 'status-online' : '');
            if (!active) el.style.border = '1px solid rgba(255,255,255,0.06)';
        };
        updateTag('tag-bot',  d.bot.status === 'online');
        updateTag('tag-graph', d.running);
        updateTag('tag-edge',  d.edge_running);

        // --- Grafo stats ---
        const nodesEl = document.getElementById('stat-nodes');
        const edgesEl = document.getElementById('stat-edges');
        animateValue(nodesEl, parseInt(nodesEl?.textContent || '0'), d.graph.nodes || 0, 700);
        animateValue(edgesEl, parseInt(edgesEl?.textContent || '0'), d.graph.edges || 0, 700);
        const densityEl = document.getElementById('stat-density');
        if (densityEl) densityEl.textContent = d.graph.density;

        // --- Bot Telegram ---
        const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        setEl('bot-uptime',    d.bot.uptime);
        animateValue(document.getElementById('bot-msg-in'),  parseInt(document.getElementById('bot-msg-in')?.textContent || '0'), d.bot.msg_in || 0, 600);
        animateValue(document.getElementById('bot-msg-out'), parseInt(document.getElementById('bot-msg-out')?.textContent || '0'), d.bot.msg_out || 0, 600);
        setEl('bot-audio-in',  d.bot.audio_in);
        setEl('bot-audio-out', d.bot.audio_out);
        setEl('bot-diagrams',  d.bot.diagrams);
        setEl('bot-chats',     d.bot.active_chats);

        // --- Chat Log do Bot ---
        const chatLogEl = document.getElementById('bot-chat-log');
        if (d.bot.last_messages && d.bot.last_messages.length > 0) {
            chatLogEl.innerHTML = d.bot.last_messages.map(m => `
                <div style="margin-bottom: 15px;">
                    <div style="color: var(--cyan); font-weight: 700; font-size: 0.7rem; margin-bottom: 4px;">USUÁRIO (${d.bot.last_activity || 'Recente'})</div>
                    <div style="color: #fff; background: rgba(255,255,255,0.04); padding: 8px 12px; border-radius: 8px; font-size: 0.8rem;">${m.u}</div>
                </div>
                <div style="margin-bottom: 15px; padding-left: 15px;">
                    <div style="color: var(--accent); font-weight: 700; font-size: 0.7rem; margin-bottom: 4px;">NEURAL AGENT</div>
                    <div style="color: #94a3b8; border-left: 2px solid var(--accent); padding-left: 10px; font-size: 0.8rem;">${m.a}</div>
                </div>
            `).join('');
        }

        // --- Sistema Core ---
        setEl('sys-os',      d.telemetry.os);
        setEl('sys-python',  d.telemetry.python_v);
        setEl('sys-boot',    d.telemetry.boot_time);
        setEl('sys-disk',    (d.telemetry.disk_percent || 0) + '%');
        setEl('sys-thermal', d.telemetry.thermal || 'Normal');
        setEl('sys-model',   d.telemetry.model || '...');

        // --- RAG Indexação ---
        const idx = d.bot.index_status || { percentage: 0, indexed: 0, total: 0 };
        const idxPct = parseInt(idx.percentage) || 0;
        animateValue(document.getElementById('stat-index'), prevTelemetry.index, idxPct, 800);
        prevTelemetry.index = idxPct;
        setEl('bot-index-percent', idxPct);
        document.getElementById('bar-index').style.width = idxPct + '%';
        setEl('stat-index-files', `${idx.indexed}/${idx.total}`);
        setEl('stat-index-questions', idx.questions || 0);

        // --- Distribuição de Disciplinas ---
        const areaEl = document.getElementById('index-areas');
        if (idx.areas && areaEl) {
            areaEl.innerHTML = Object.entries(idx.areas)
                .sort((a, b) => b[1].total - a[1].total)
                .map(([name, stat]) => {
                    const p = Math.round((stat.indexed / stat.total) * 100);
                    return `
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; align-items: center;">
                            <span style="color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px;" title="${name}">${name}</span>
                            <span style="color: ${p === 100 ? 'var(--green)' : 'var(--cyan)'}; font-weight: 700; font-family: monospace;">
                                ${p}% (${stat.indexed}/${stat.total})
                            </span>
                        </div>
                    `;
                }).join('');
        }

        // --- Console de Logs com Flash ---
        const logRes = await fetch('/api/logs');
        const logs = await logRes.json();
        const consoleEl = document.getElementById('home-console');

        let filteredLogs = logs;
        if (activeLogFilter === 'graph') {
            filteredLogs = logs.filter(l => l.includes('[GRAPH]') || l.includes('[SYNC]') || l.toLowerCase().includes('curator'));
        } else if (activeLogFilter === 'bot') {
            filteredLogs = logs.filter(l => l.includes('[BOT]'));
        }

        const prevCount = consoleEl.querySelectorAll('.log-line').length;
        const newCount = filteredLogs.length;

        consoleEl.innerHTML = filteredLogs.map((l, i) => {
            let style = '';
            if (l.includes('[ERROR]') || l.includes('Exception') || l.includes('Error')) style = 'color: var(--red);';
            else if (l.includes('[WARNING]')) style = 'color: var(--amber);';
            else if (l.includes('[GRAPH]'))   style = 'color: var(--cyan);';
            else if (l.includes('[BOT]'))     style = 'color: var(--accent);';
            const isNew = i >= prevCount;
            return `<div class="log-line${isNew ? ' flash-new' : ''}" style="${style}">> ${l}</div>`;
        }).join('') || '<div class="log-line" style="color: var(--text-muted);">> Nenhum registro sob este filtro.</div>';

        consoleEl.scrollTop = consoleEl.scrollHeight;

        // --- Sala de Estudos (carrega só se ativa) ---
        if (document.getElementById('page-study').classList.contains('active')) {
            await loadSummariesData();
        }

    } catch (e) { console.error('Erro na sincronização de telemetria:', e); }
}

function setLogFilter(filterType) {
    activeLogFilter = filterType;
    document.querySelectorAll('.filter-tag').forEach(tag => {
        tag.classList.remove('active');
        if (tag.classList.contains(filterType)) tag.classList.add('active');
    });
    updateTelemetry();
}

// ============================================================
// SALA DE ESTUDOS — Skeletons, Filtros e Paginação
// ============================================================
function showStudySkeletons() {
    const listEl = document.getElementById('study-list');
    listEl.innerHTML = Array(6).fill(0).map(() => `
        <div class="skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line long" style="margin-top:16px;"></div>
            <div class="skeleton-line medium"></div>
        </div>
    `).join('');
}

async function loadSummariesData() {
    try {
        const sRes = await fetch('/api/summaries');
        allSummaries = await sRes.json();
        renderSummaries();
    } catch (e) { console.error('Erro ao ler resumos:', e); }
}

function renderSummaries() {
    let filtered = allSummaries;
    if (studySearchTerm) {
        const query = studySearchTerm.toLowerCase();
        filtered = allSummaries.filter(f =>
            f.name.toLowerCase().includes(query) ||
            (f.path && f.path.toLowerCase().includes(query))
        );
    }

    const totalItems  = filtered.length;
    const totalPages  = Math.max(1, Math.ceil(totalItems / studyPageSize));
    if (studyCurrentPage > totalPages) studyCurrentPage = totalPages;
    if (studyCurrentPage < 1) studyCurrentPage = 1;

    const startIndex = (studyCurrentPage - 1) * studyPageSize;
    const paginated  = filtered.slice(startIndex, startIndex + studyPageSize);

    const listEl = document.getElementById('study-list');
    if (paginated.length === 0) {
        listEl.innerHTML = '<p style="color: #64748b; grid-column: 1/-1; text-align: center; padding: 60px 0; font-size: 0.9rem;">Nenhum resumo encontrado.</p>';
    } else {
        listEl.innerHTML = paginated.map(f => {
            const cleanName = f.name.split('_').slice(1, -1).join(' ') || f.name;
            return `
                <div class="card" onclick="window.open('/api/summary/${f.path}', '_blank')" style="cursor: pointer; border-left: 3px solid var(--cyan);">
                    <h3>${cleanName}</h3>
                    <p style="font-size: 0.8rem; color: #64748b; margin-top: 8px;">Gerado em: ${f.date}</p>
                    <div style="margin-top: 18px; display: flex; align-items: center; gap: 8px; color: var(--cyan); font-size: 0.7rem; font-weight: 800; letter-spacing: 1px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                        ABRIR RESUMO
                    </div>
                </div>
            `;
        }).join('');
    }

    const pagControlsEl = document.getElementById('study-pagination');
    if (totalPages > 1) {
        pagControlsEl.style.display = 'flex';
        document.getElementById('study-page-info').textContent = `Página ${studyCurrentPage} de ${totalPages} (${totalItems})`;
        document.getElementById('study-prev-btn').disabled = studyCurrentPage === 1;
        document.getElementById('study-next-btn').disabled = studyCurrentPage === totalPages;
    } else {
        pagControlsEl.style.display = 'none';
    }
}

function handleStudySearch(term) {
    studySearchTerm = term;
    studyCurrentPage = 1;
    renderSummaries();
}

function changeStudyPage(direction) {
    studyCurrentPage += direction;
    renderSummaries();
}

// ============================================================
// ENGINE DO GRAFO NEURAL (D3.js)
// ============================================================
let simulation, svg, g, nodes = [], edges = [], activeFilter = 'all';
const tooltipEl = document.getElementById('tooltip');

const zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 5])
    .on('zoom', (e) => {
        g.attr('transform', e.transform);
        localStorage.setItem('flos_graph_zoom', JSON.stringify({ x: e.transform.x, y: e.transform.y, k: e.transform.k }));
    });

function initGraph() {
    if (svg) return;
    const container = document.getElementById('graph-canvas');
    const width = container.clientWidth, height = container.clientHeight;

    if (!document.getElementById('graph-loading')) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'graph-loading';
        loadingDiv.className = 'canvas-loading';
        loadingDiv.innerHTML = `<span class="spinner"></span><span class="canvas-loading-text">Mapeando Rede Neural...</span>`;
        container.appendChild(loadingDiv);
    }

    svg = d3.select('#graph-canvas').append('svg').attr('width', '100%').attr('height', '100%');
    g = svg.append('g');
    svg.call(zoomBehavior);

    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(120))
        .force('charge', d3.forceManyBody().strength(-350))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(45));

    loadGraphData(true);
    setInterval(() => loadGraphData(false), 15000);

    const searchInput = document.getElementById('graph-search');
    const resultsDiv  = document.getElementById('graph-autocomplete-results');

    searchInput.addEventListener('input', (e) => handleGraphSearchInput(e.target.value));
    searchInput.addEventListener('focus', (e) => {
        if (e.target.value.length > 0) resultsDiv.style.display = 'block';
    });
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) resultsDiv.style.display = 'none';
    });
}

async function loadGraphData(firstLoad = false) {
    try {
        const data = await d3.json('/api/graph');
        nodes = data.nodes;
        edges = data.edges;

        let savedPositions = {};
        try { savedPositions = JSON.parse(localStorage.getItem('flos_graph_node_positions') || '{}'); } catch (_) {}
        nodes.forEach(n => {
            if (savedPositions[n.id]) {
                n.x = savedPositions[n.id].x;
                n.y = savedPositions[n.id].y;
                n.fx = savedPositions[n.id].x;
                n.fy = savedPositions[n.id].y;
            }
        });

        const loadingDiv = document.getElementById('graph-loading');
        if (loadingDiv) { loadingDiv.style.opacity = '0'; setTimeout(() => loadingDiv.style.display = 'none', 500); }

        updateGraph();

        if (firstLoad) {
            const z = JSON.parse(localStorage.getItem('flos_graph_zoom') || 'null');
            if (z) svg.call(zoomBehavior.transform, d3.zoomIdentity.translate(z.x, z.y).scale(z.k));
        }
    } catch (e) { console.error('Erro ao carregar dados do grafo:', e); }
}

function filterGraph(type) {
    activeFilter = type;
    document.querySelectorAll('#graph-filters .btn').forEach(btn => btn.classList.remove('primary'));
    event.currentTarget.classList.add('primary');
    updateGraph();
}

function updateGraph() {
    let filteredNodes = nodes;
    if (activeFilter !== 'all') filteredNodes = nodes.filter(n => n.type === activeFilter || n.id === 'mestre');
    const ids = new Set(filteredNodes.map(n => n.id));
    let filteredEdges = edges.filter(e => ids.has(e.source.id || e.source) && ids.has(e.target.id || e.target));

    const link = g.selectAll('.link')
        .data(filteredEdges, d => (d.source.id || d.source) + '-' + (d.target.id || d.target))
        .join('line').attr('class', 'link')
        .style('stroke', 'rgba(255,255,255,0.05)')
        .style('stroke-width', 1.2);

    const node = g.selectAll('.node')
        .data(filteredNodes, d => d.id)
        .join('g').attr('class', 'node')
        .call(d3.drag()
            .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.2).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag',  (e, d) => { d.fx = e.x; d.fy = e.y; })
            .on('end',   (e, d) => {
                if (!e.active) simulation.alphaTarget(0);
                d.fx = d.x; d.fy = d.y;
                let sp = {};
                try { sp = JSON.parse(localStorage.getItem('flos_graph_node_positions') || '{}'); } catch (_) {}
                sp[d.id] = { x: d.x, y: d.y };
                localStorage.setItem('flos_graph_node_positions', JSON.stringify(sp));
            }));

    node.selectAll('circle').data(d => [d]).join('circle')
        .attr('r', d => d.id === 'mestre' ? 22 : 9)
        .attr('fill', d => {
            if (d.id === 'mestre') return 'var(--accent)';
            if (d.type === 'mba')  return 'var(--green)';
            if (d.type === 'work') return '#f59e0b';
            return 'var(--cyan)';
        })
        .style('cursor', 'pointer')
        .style('filter', d => d.id === 'mestre' ? 'drop-shadow(0 0 8px rgba(168,85,247,0.6))' : 'drop-shadow(0 0 4px rgba(255,255,255,0.08))')
        .on('mouseover', (e, d) => {
            const cCount = edges.filter(ed => (ed.source.id || ed.source) === d.id || (ed.target.id || ed.target) === d.id).length;
            tooltipEl.innerHTML = `
                <div class="tooltip-title">${d.title}</div>
                <div class="tooltip-meta">ID: <span>${d.id}</span></div>
                <div class="tooltip-meta">Tipo: <span style="text-transform:uppercase">${d.type || 'N/A'}</span></div>
                <div class="tooltip-meta">Grau: <span class="tooltip-connections">${cCount} conexões</span></div>
            `;
            tooltipEl.style.opacity = '1';
        })
        .on('mousemove', (e) => {
            tooltipEl.style.left = (e.clientX + 16) + 'px';
            tooltipEl.style.top  = (e.clientY + 16) + 'px';
        })
        .on('mouseout', () => { tooltipEl.style.opacity = '0'; })
        .on('click',    (e, d) => openNodePanel(d));

    node.selectAll('text').data(d => [d]).join('text')
        .text(d => d.title)
        .attr('dy', 22).attr('text-anchor', 'middle')
        .style('fill', 'var(--text-muted)').style('font-size', '9px')
        .style('font-weight', '500').style('pointer-events', 'none')
        .style('font-family', "'Inter', sans-serif");

    simulation.nodes(filteredNodes);
    simulation.force('link').links(filteredEdges);
    simulation.alpha(0.3).restart();

    simulation.on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function resetGraphLayout() {
    confirmAction('Resetar Layout do Grafo?',
        'Todas as posições personalizadas dos nós serão redefinidas. Deseja prosseguir?',
        () => {
            localStorage.removeItem('flos_graph_node_positions');
            localStorage.removeItem('flos_graph_zoom');
            nodes.forEach(n => { n.fx = null; n.fy = null; });
            const container = document.getElementById('graph-canvas');
            svg.transition().duration(600).call(zoomBehavior.transform, d3.zoomIdentity);
            updateGraph();
            showToast('Layout do grafo redefinido.', 'info');
        }
    );
}

// ============================================================
// AUTOCOMPLETE COM STAGGER
// ============================================================
function handleGraphSearchInput(term) {
    const resultsDiv = document.getElementById('graph-autocomplete-results');
    if (!term) { resultsDiv.style.display = 'none'; return; }
    const query = term.toLowerCase();
    const matches = nodes.filter(n =>
        n.title.toLowerCase().includes(query) || n.id.toLowerCase().includes(query)
    ).slice(0, 8);

    if (matches.length > 0) {
        resultsDiv.innerHTML = matches.map((n, i) => `
            <div class="autocomplete-item" onclick="selectGraphNode('${n.id}')"
                 style="animation-delay: ${i * 45}ms;">
                <span>${n.title}</span>
                <span class="autocomplete-type" style="color: ${
                    n.type === 'mba' ? 'var(--green)' :
                    n.type === 'work' ? 'var(--amber)' : 'var(--cyan)'
                };">${n.type || 'mestre'}</span>
            </div>
        `).join('');
        resultsDiv.style.display = 'block';
    } else {
        resultsDiv.innerHTML = `<div style="padding: 12px 15px; font-size: 0.8rem; color: var(--text-muted);">Nenhum nó encontrado</div>`;
        resultsDiv.style.display = 'block';
    }
}

function selectGraphNode(nodeId) {
    document.getElementById('graph-autocomplete-results').style.display = 'none';
    document.getElementById('graph-search').value = '';
    const targetNode = nodes.find(n => n.id === nodeId);
    if (!targetNode) return;
    openNodePanel(targetNode);
    focusNode(targetNode);
}

function focusNode(targetNode) {
    const container = document.getElementById('graph-canvas');
    const width = container.clientWidth, height = container.clientHeight;
    const scale = 1.6;
    const x = width / 2 - targetNode.x * scale;
    const y = height / 2 - targetNode.y * scale;
    svg.transition().duration(800).call(zoomBehavior.transform, d3.zoomIdentity.translate(x, y).scale(scale));

    const circle = g.selectAll('.node').filter(d => d.id === targetNode.id).select('circle');
    circle.transition().duration(200)
        .attr('r', targetNode.id === 'mestre' ? 32 : 18)
        .style('stroke', '#fff').style('stroke-width', '3px')
        .transition().duration(900)
        .attr('r', targetNode.id === 'mestre' ? 22 : 9)
        .style('stroke', 'none');
}

// ============================================================
// PAINEL LATERAL DO NÓ
// ============================================================
function openNodePanel(nodeData) {
    const panel   = document.getElementById('node-panel');
    const content = document.getElementById('node-panel-content');

    const directEdges = edges.filter(e =>
        (e.source.id || e.source) === nodeData.id ||
        (e.target.id  || e.target)  === nodeData.id
    );

    const connectionsHtml = directEdges.map(e => {
        const otherId   = (e.source.id || e.source) === nodeData.id ? (e.target.id || e.target) : (e.source.id || e.source);
        const otherNode = nodes.find(n => n.id === otherId);
        const otherTitle = otherNode ? otherNode.title : otherId;
        return `<div class="autocomplete-item" onclick="selectGraphNode('${otherId}')" style="margin-bottom:6px;border-radius:8px;border:1px solid var(--border);">
            <span>${otherTitle}</span>
            <span style="font-size:0.65rem;color:var(--text-muted);">${otherId}</span>
        </div>`;
    }).join('') || '<p style="font-size:0.8rem;color:var(--text-muted);">Sem conexões de vizinhança direta.</p>';

    content.innerHTML = `
        <h2 style="font-family:'Outfit';font-size:1.5rem;font-weight:800;color:white;margin-top:0;margin-bottom:5px;">${nodeData.title}</h2>
        <p style="color:var(--cyan);font-weight:700;font-size:0.72rem;letter-spacing:1.5px;text-transform:uppercase;margin-top:0;margin-bottom:25px;">${nodeData.type || 'Nó Mestre'}</p>

        <div style="margin-bottom:22px;border-top:1px solid var(--border);padding-top:18px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">Identificador Neural</h4>
            <div style="font-family:monospace;font-size:0.82rem;color:#fff;background:rgba(0,0,0,0.25);padding:10px 14px;border-radius:10px;word-break:break-all;border:1px solid var(--border);">${nodeData.id}</div>
        </div>

        <div style="margin-bottom:22px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">Rede Conectada (${directEdges.length} arestas)</h4>
            <div style="max-height:220px;overflow-y:auto;">${connectionsHtml}</div>
        </div>

        <div style="margin-top:auto;border-top:1px solid var(--border);padding-top:18px;display:flex;gap:10px;">
            <button class="btn primary" onclick="focusNode(nodes.find(n=>n.id==='${nodeData.id}'))" style="flex:1;padding:10px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M22 12h-4M6 12H2M12 6V2M12 22v-4"></path></svg>
                Focar Nó
            </button>
            <button class="btn" onclick="window.open('/api/summary/'+encodeURIComponent('${nodeData.id}_resumo.md'),'_blank')" style="flex:1;padding:10px;font-size:0.7rem;">
                Ver Resumo ↗
            </button>
        </div>
    `;

    panel.classList.add('open');
}

function closeNodePanel() {
    document.getElementById('node-panel').classList.remove('open');
}

// ============================================================
// INICIALIZAÇÃO
// ============================================================
window.addEventListener('DOMContentLoaded', () => {
    // --- Ripple nos botões e nav-items ---
    document.addEventListener('click', (e) => {
        const target = e.target.closest('.btn, .nav-item');
        if (target) createRipple(target, e);
    });

    // --- Skeleton na Sala de Estudos até os dados chegarem ---
    showStudySkeletons();

    // --- Event listener de busca na Sala de Estudos ---
    const studySearch = document.getElementById('study-search');
    if (studySearch) studySearch.addEventListener('input', (e) => handleStudySearch(e.target.value));

    // --- Inicia pílula na posição correta (Home, índice 0) ---
    updateNavPill('home');

    // --- Inicia telemetria ---
    setInterval(updateTelemetry, 3000);
    updateTelemetry();

    // --- EventSource SSE para logs em tempo real ---
    const source = new EventSource('/api/update-stream');
    source.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.log) {
                const logLine = data.log;
                const consoleEl = document.getElementById('home-console');
                if (consoleEl) {
                    const row = document.createElement('div');
                    row.className = 'log-line flash-new';
                    if (logLine.includes('[ERROR]') || logLine.includes('Exception') || logLine.includes('Error')) {
                        row.style.color = 'var(--red)';
                    } else if (logLine.includes('[WARNING]')) {
                        row.style.color = 'var(--amber)';
                    } else if (logLine.includes('[GRAPH]') || logLine.includes('✨ Sincronizando')) {
                        row.style.color = 'var(--cyan)';
                    } else if (logLine.includes('[BOT]')) {
                        row.style.color = 'var(--accent)';
                    }
                    row.textContent = `> ${logLine}`;
                    consoleEl.appendChild(row);
                    consoleEl.scrollTop = consoleEl.scrollHeight;
                    while (consoleEl.children.length > 80) {
                        consoleEl.removeChild(consoleEl.firstChild);
                    }
                }
                
                const match = logLine.match(/✨ Sincronizando:\s+(\d+)\/(\d+)\s+arquivos/);
                if (match) {
                    const current = parseInt(match[1]);
                    const total = parseInt(match[2]);
                    const pct = Math.round((current / total) * 100);
                    
                    const statIdx = document.getElementById('stat-index');
                    if (statIdx) statIdx.textContent = pct;
                    
                    const barIdx = document.getElementById('bar-index');
                    if (barIdx) barIdx.style.width = pct + '%';
                    
                    const fileIdx = document.getElementById('stat-index-files');
                    if (fileIdx) fileIdx.textContent = `${current}/${total}`;
                }
            }
        } catch (e) {
            console.error("Erro ao ler chunk SSE:", e);
        }
    };
});

// ============================================================
// SISTEMA DA RINHA DE GRAFOS
// ============================================================
let rinhaOpponents = [];
let p1GraphData = null;
let currentBattleSimP1 = null;
let currentBattleSimP2 = null;
let activeBattleInterval = null;
let imperialDecrees = {};
let currentBattleOpponentId = null;
let rinhaMode = 'classic';
let rinhaFights = [];

const VOCABULARY = [
    "NeuralNet", "DeepLearning", "AgentBot", "NLP_Core", "DataLake", "SQL_Engine", "DockerHub", "PythonSDK", "ETL_Pipeline", "REST_API", 
    "DataStream", "K8s_Cluster", "PyTorchModel", "SparkCluster", "NoSQL_DB", "CloudSync", "GitRepo", "RustCompiler", "LLM_Orchestrator", "RAG_Index", 
    "Embeddings", "FastAPI_Srv", "PandasLib", "PostgresDB", "RedisCache", "KafkaBroker", "AirflowDAG", "AWS_S3", "BigQuery", "SnowflakeDW", 
    "dbt_Model", "GraphQL_API", "TensorFlow", "ScikitLearn", "MLOps_Flow", "ReactUI", "VueApp", "TypeScript", "NodeJS", "LinuxKernel", 
    "NginxProxy", "MongoDB", "ElasticSearch", "Neo4jGraph", "VectorStore", "SemanticSearch", "BTreeIndex", "MemoryCache", "RabbitMQ", "DataFlow", 
    "QueryParser", "DataTable", "JsonSchema", "YamlConfig", "WebWorker", "CronJob", "EventTrigger", "SlackAlert", "Prometheus", "Grafana", 
    "LogCollector", "JaegerTrace", "OtelSpan", "RouterGateway", "Microservice", "Repository", "CognitiveModel", "TemplateEngine", "TailwindCSS", "D3_Renderer", 
    "HTML5_Canvas", "SVG_Vector", "ReduxState", "ReactHook", "API_Gateway", "AuthToken", "SessionStore", "CookieJar", "CorsPolicy", "SSL_Cert", 
    "DNS_Resolver", "IP_Router", "LoadBalancer", "ReverseProxy", "TaskQueue", "JobScheduler", "MessageBus", "TelemetryUnit", "AuditLogger", "DataSanitizer",
    "VectorIndex", "SemanticMap", "EmbeddingDB", "TextChunker", "ChunkMerger", "ParserEngine", "TaxonomyMap", "KnowledgeGraph", "EdgeAuditor", "LineageTracker"
];

// BFS para calcular a distância máxima
function bfsMaxDist(startId, edges) {
    let queue = [startId];
    let visited = {};
    visited[startId] = 0;
    let maxD = 0;
    
    let adj = {};
    edges.forEach(e => {
        let s = e.source.id || e.source;
        let t = e.target.id || e.target;
        if(!adj[s]) adj[s] = [];
        if(!adj[t]) adj[t] = [];
        adj[s].push(t);
        adj[t].push(s);
    });
    
    while(queue.length > 0) {
        let current = queue.shift();
        let dist = visited[current];
        maxD = Math.max(maxD, dist);
        
        let neighbors = adj[current] || [];
        neighbors.forEach(n => {
            if(visited[n] === undefined) {
                visited[n] = dist + 1;
                queue.push(n);
            }
        });
    }
    return maxD;
}

// Identifica os super-hubs do grafo (top 15% de nós por conectividade)
function getSuperHubs(graph) {
    let degMap = {};
    graph.nodes.forEach(n => degMap[n.id] = 0);
    graph.edges.forEach(e => {
        let s = e.source.id || e.source;
        let t = e.target.id || e.target;
        degMap[s] = (degMap[s] || 0) + 1;
        degMap[t] = (degMap[t] || 0) + 1;
    });
    
    let sortedNodes = [...graph.nodes].map(n => ({ id: n.id, deg: degMap[n.id] || 0 }))
                                       .sort((a, b) => b.deg - a.deg);
    
    let numHubs = Math.max(1, Math.round(graph.nodes.length * 0.15));
    return new Set(sortedNodes.slice(0, numHubs).map(n => n.id));
}

// Avalia métricas baseadas na capacidade de agrupar sub-nós ao redor de super-hubs
function evaluateGraphMetrics(graph) {
    let nodeCount = graph.nodes.length;
    let edgeCount = graph.edges.length;
    if(nodeCount === 0) return { grouping: 0, visual: 0, flow: 0, score: 0 };
    
    let degMap = {};
    graph.nodes.forEach(n => degMap[n.id] = 0);
    graph.edges.forEach(e => {
        let s = e.source.id || e.source;
        let t = e.target.id || e.target;
        degMap[s] = (degMap[s] || 0) + 1;
        degMap[t] = (degMap[t] || 0) + 1;
    });
    
    let superHubs = getSuperHubs(graph);
    
    // Adjacência
    let adj = {};
    graph.edges.forEach(e => {
        let s = e.source.id || e.source;
        let t = e.target.id || e.target;
        if(!adj[s]) adj[s] = [];
        if(!adj[t]) adj[t] = [];
        adj[s].push(t);
        adj[t].push(s);
    });
    
    // 1. CAPACIDADE DE AGRUPAMENTO (Capacidade de agrupar sub-nós)
    let groupedCount = 0;
    graph.nodes.forEach(n => {
        if (superHubs.has(n.id)) {
            groupedCount++;
        } else {
            let neighbors = adj[n.id] || [];
            let connectedToHub = neighbors.some(neighId => superHubs.has(neighId));
            if (connectedToHub) groupedCount++;
        }
    });
    let groupingScore = Math.max(10, Math.min(100, Math.round((groupedCount / nodeCount) * 100)));
    
    // 2. HARMONIA VISUAL / CLAREZA DE AGRUPAMENTO
    let totalClusterVariance = 0;
    superHubs.forEach(hubId => {
        let count = (adj[hubId] || []).length;
        let diff = Math.max(0, 4 - count) + Math.max(0, count - 12);
        totalClusterVariance += diff;
    });
    let avgVariance = superHubs.size > 0 ? totalClusterVariance / superHubs.size : 10;
    let visualScore = Math.max(10, Math.min(100, Math.round(100 - (avgVariance * 7.5))));
    
    // 3. VELOCIDADE DE FLUXO (Propagação de dados a partir dos hubs)
    let diameterApprox = 5;
    if(superHubs.size > 0) {
        let maxDist = 0;
        superHubs.forEach(hubId => {
            let dist = bfsMaxDist(hubId, graph.edges);
            if(dist > maxDist) maxDist = dist;
        });
        diameterApprox = maxDist;
    }
    let totalDeg = Object.values(degMap).reduce((a, b) => a + b, 0);
    let avgDegree = totalDeg / nodeCount;
    let flowScore = Math.max(10, Math.min(100, Math.round(100 - (diameterApprox * 7) + (avgDegree * 4))));
    
    let overallScore = Math.round(groupingScore * 0.45 + visualScore * 0.35 + flowScore * 0.20);
    
    return {
        grouping: groupingScore,
        visual: visualScore,
        flow: flowScore,
        score: overallScore
    };
}

// Inicializa a aba de Rinha
async function initRinha() {
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Carregando...';
    
    if (!p1GraphData) {
        await loadP1GraphData('obsidian');
    }
    
    rinhaOpponents = generateOpponents();
    badge.textContent = 'Pronto para Combate';
    badge.className = 'bot-status-tag status-online';
}

// Carrega dados do desafiante P1
async function loadP1GraphData(source) {
    if (source === 'obsidian') {
        try {
            const data = await d3.json('/api/graph');
            p1GraphData = {
                id: 'obsidian',
                name: 'Seu Grafo Neural (Obsidian)',
                nodes: data.nodes.map(n => ({ id: n.id, label: n.title })),
                edges: data.edges.map(e => ({ source: e.source.id || e.source, target: e.target.id || e.target }))
            };
        } catch (e) {
            console.error('Erro ao carregar Grafo principal:', e);
            p1GraphData = makeP1Procedural('random', 80);
        }
    } else {
        p1GraphData = makeP1Procedural(source, 60);
    }
    document.getElementById('battle-versus-title').textContent = `${p1GraphData.name} vs ...`;
}

// Muda o desafiante principal P1
async function changeP1Graph() {
    const select = document.getElementById('rinha-p1-select');
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Carregando P1...';
    await loadP1GraphData(select.value);
    badge.textContent = 'Pronto para Combate';
    resetRinhaTournament();
}

// Procedural para P1 (com nomes realistas em todos os nós)
function makeP1Procedural(type, size) {
    let mock = { id: type, name: '', nodes: [], edges: [] };
    
    for(let j = 0; j < size; j++) {
        let name = VOCABULARY[j % VOCABULARY.length] + "_" + j;
        mock.nodes.push({ id: `${j}`, label: name });
    }
    
    if (type === 'random') {
        mock.name = 'P1: Grafo Aleatório (ER)';
        for(let j = 0; j < size; j++) {
            for(let k = j + 1; k < size; k++) {
                if(Math.random() < 0.05) mock.edges.push({ source: `${j}`, target: `${k}` });
            }
        }
    } else if (type === 'scalefree') {
        mock.name = 'P1: Grafo Sem Escala (BA)';
        mock.edges.push({ source: '0', target: '1' });
        for(let j = 2; j < size; j++) {
            let target = Math.floor(Math.random() * j);
            mock.edges.push({ source: `${j}`, target: `${target}` });
        }
    } else {
        mock.name = 'P1: Grafo Roda';
        mock.nodes[0].label = "MasterHub";
        for(let j = 1; j < size; j++) {
            mock.edges.push({ source: '0', target: `${j}` });
            if(j > 1) mock.edges.push({ source: `${j-1}`, target: `${j}` });
        }
        if(size > 2) mock.edges.push({ source: `${size-1}`, target: '1' });
    }
    return mock;
}

// Gera o array de 100 topologias adversárias
function generateOpponents() {
    let list = [];
    const types = ['Estrela', 'Roda', 'Grid', 'Mundo Pequeno (WS)', 'Sem Escala (BA)', 'Aleatório (ER)', 'Árvore Binária', 'Anel Ciclo', 'Lollipop', 'Bipartido'];
    
    for(let i = 1; i <= 100; i++) {
        let type = types[(i - 1) % types.length];
        let numNodes = 20 + (i % 8) * 10;
        let name = `Oponente #${i}: ${type} [T-${numNodes}]`;
        let graphData = { id: i, name: name, type: type, nodes: [], edges: [] };
        
        for(let j = 0; j < numNodes; j++) {
            let word = VOCABULARY[(j + i * 3) % VOCABULARY.length];
            let nodeName = `${word}_${j}`;
            graphData.nodes.push({ id: `${j}`, label: nodeName });
        }
        
        if (type === 'Estrela') {
            graphData.nodes[0].label = "CentralHub";
            for(let j = 1; j < numNodes; j++) {
                graphData.edges.push({ source: '0', target: `${j}` });
            }
        } else if (type === 'Roda') {
            graphData.nodes[0].label = "WheelHub";
            for(let j = 1; j < numNodes; j++) {
                graphData.edges.push({ source: '0', target: `${j}` });
                if(j > 1) graphData.edges.push({ source: `${j-1}`, target: `${j}` });
            }
            if(numNodes > 2) graphData.edges.push({ source: `${numNodes-1}`, target: '1' });
        } else if (type === 'Grid') {
            let cols = Math.floor(Math.sqrt(numNodes));
            let rows = Math.ceil(numNodes / cols);
            for(let r = 0; r < rows; r++) {
                for(let c = 0; c < cols; c++) {
                    let idx = r * cols + c;
                    if(idx < numNodes) {
                        if(c > 0) graphData.edges.push({ source: `${idx-1}`, target: `${idx}` });
                        if(r > 0) graphData.edges.push({ source: `${idx-cols}`, target: `${idx}` });
                    }
                }
            }
        } else if (type === 'Anel Ciclo') {
            for(let j = 0; j < numNodes; j++) {
                if(j > 0) graphData.edges.push({ source: `${j-1}`, target: `${j}` });
            }
            if(numNodes > 1) graphData.edges.push({ source: `${numNodes-1}`, target: '0' });
        } else if (type === 'Árvore Binária') {
            graphData.nodes[0].label = "RootNode";
            for(let j = 1; j < numNodes; j++) {
                let parent = Math.floor((j - 1) / 2);
                graphData.edges.push({ source: `${parent}`, target: `${j}` });
            }
        } else if (type === 'Aleatório (ER)') {
            let p = 0.05 + (i % 5) * 0.02;
            for(let j = 0; j < numNodes; j++) {
                for(let k = j + 1; k < numNodes; k++) {
                    if(Math.random() < p) {
                        graphData.edges.push({ source: `${j}`, target: `${k}` });
                    }
                }
            }
        } else if (type === 'Sem Escala (BA)') {
            graphData.nodes[0].label = "SeedHubA";
            graphData.nodes[1].label = "SeedHubB";
            graphData.edges.push({ source: '0', target: '1' });
            let degrees = { '0': 1, '1': 1 };
            let totalDegree = 2;
            for(let j = 2; j < numNodes; j++) {
                let targets = [];
                let m = (i % 2) + 1;
                for(let attempts = 0; attempts < 10 && targets.length < m; attempts++) {
                    let cand = Math.floor(Math.random() * j);
                    let prob = (degrees[cand] || 1) / totalDegree;
                    if(Math.random() < prob && !targets.includes(cand)) {
                        targets.push(cand);
                    }
                }
                if(targets.length === 0) targets.push(Math.floor(Math.random() * j));
                targets.forEach(tgt => {
                    graphData.edges.push({ source: `${j}`, target: `${tgt}` });
                    degrees[j] = (degrees[j] || 0) + 1;
                    degrees[tgt] = (degrees[tgt] || 0) + 1;
                    totalDegree += 2;
                });
            }
        } else if (type === 'Mundo Pequeno (WS)') {
            let k_neighbors = 4;
            let beta = 0.2 + (i % 4) * 0.08;
            for(let j = 0; j < numNodes; j++) {
                for(let step = 1; step <= k_neighbors / 2; step++) {
                    let target = (j + step) % numNodes;
                    graphData.edges.push({ source: `${j}`, target: `${target}` });
                }
            }
            graphData.edges.forEach(edge => {
                if(Math.random() < beta) {
                    edge.target = `${Math.floor(Math.random() * numNodes)}`;
                }
            });
        } else if (type === 'Lollipop') {
            let headSize = Math.floor(numNodes * 0.65);
            for(let j = 0; j < headSize; j++) {
                for(let k = j + 1; k < headSize; k++) {
                    graphData.edges.push({ source: `${j}`, target: `${k}` });
                }
            }
            for(let j = headSize; j < numNodes; j++) {
                if (j === headSize) {
                    graphData.edges.push({ source: `${headSize - 1}`, target: `${j}` });
                } else {
                    graphData.edges.push({ source: `${j-1}`, target: `${j}` });
                }
            }
        } else {
            let setA = Math.floor(numNodes * 0.35);
            for(let j = 0; j < numNodes; j++) {
                if (j >= setA) {
                    let connCount = 1 + (i % 2);
                    for(let c = 0; c < connCount; c++) {
                        let target = Math.floor(Math.random() * setA);
                        graphData.edges.push({ source: `${target}`, target: `${j}` });
                    }
                }
            }
        }
        list.push(graphData);
    }
    return list;
}

// Controla mudança de modo
function changeRinhaMode() {
    const select = document.getElementById('rinha-mode-select');
    rinhaMode = select.value;
    const btn = document.getElementById('btn-run-rinha');
    if (rinhaMode === 'evolutionary') {
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Iniciar Evolução`;
    } else if (rinhaMode === 'gemma4') {
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Evolução Gemma4`;
    } else {
        btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Iniciar Rinha Geral`;
    }
    resetRinhaTournament();
}

// Inicia o torneio
function startRinhaTournament() {
    if (rinhaMode === 'evolutionary') {
        startEvolutionaryTournament();
    } else {
        startClassicTournament();
    }
}

// Rinha Clássica (1 contra 100)
function startClassicTournament() {
    if(!p1GraphData) {
        showToast('Aguarde carregar o Grafo Principal...', 'error');
        return;
    }
    
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Em Rinha...';
    badge.className = 'bot-status-tag';
    badge.style.borderColor = 'var(--accent)';
    badge.style.color = 'var(--accent)';
    
    const progressSection = document.getElementById('rinha-progress-section');
    const progressBar = document.getElementById('rinha-progress-bar');
    const progressLabel = document.getElementById('rinha-progress-label');
    const progressPercent = document.getElementById('rinha-progress-percent');
    
    progressSection.style.display = 'block';
    
    const p1Eval = evaluateGraphMetrics(p1GraphData);
    p1GraphData.metrics = p1Eval;
    
    let currentIdx = 0;
    const items = [];
    
    function processBatch() {
        const batchSize = 10;
        const end = Math.min(currentIdx + batchSize, rinhaOpponents.length);
        
        for(let idx = currentIdx; idx < end; idx++) {
            let opponent = rinhaOpponents[idx];
            let p2Eval = evaluateGraphMetrics(opponent);
            opponent.metrics = p2Eval;
            
            let res = 'DRAW';
            if (imperialDecrees[opponent.id]) {
                res = imperialDecrees[opponent.id] === 'P1' ? 'WIN' : 'LOSE';
            } else {
                if(p1Eval.score > p2Eval.score) res = 'WIN';
                else if(p1Eval.score < p2Eval.score) res = 'LOSE';
            }
            
            items.push({
                id: opponent.id,
                name: opponent.name,
                result: res,
                score: p2Eval.score,
                opponent: opponent
            });
        }
        
        currentIdx = end;
        let pct = Math.round((currentIdx / rinhaOpponents.length) * 100);
        progressBar.style.width = pct + '%';
        progressPercent.textContent = pct + '%';
        progressLabel.textContent = `Processando: oponente #${currentIdx} de 100`;
        
        if (currentIdx < rinhaOpponents.length) {
            setTimeout(processBatch, 30);
        } else {
            finishClassicTournament(items, p1Eval);
        }
    }
    
    setTimeout(processBatch, 40);
}

// Conclui o torneio clássico e renderiza a tabela
function finishClassicTournament(items, p1Eval) {
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Concluído';
    badge.className = 'bot-status-tag status-online';
    
    items.sort((a, b) => b.score - a.score);
    
    let p1RankPos = 0;
    while(p1RankPos < items.length && items[p1RankPos].score >= p1Eval.score) {
        p1RankPos++;
    }
    
    const tbody = document.getElementById('rinha-rank-body');
    tbody.innerHTML = '';
    
    let rankRows = [];
    items.forEach((item, index) => {
        let rankNum = index + 1;
        
        if (index === p1RankPos) {
            rankRows.push(`
                <tr class="selected" style="background: rgba(6, 182, 212, 0.15); border-left: 4px solid var(--cyan); font-weight: 700;">
                    <td style="padding-left:10px; color:var(--cyan);">#${p1RankPos + 1}</td>
                    <td>👑 ${p1GraphData.name} <span class="badge">CAMPEÃO</span></td>
                    <td style="text-align:center;"><span class="rinha-badge win">P1</span></td>
                    <td style="text-align:right; padding-right:10px; color:var(--cyan); font-family:monospace;">${p1Eval.score} pts</td>
                </tr>
            `);
        }
        
        let displayRank = rankNum;
        if(index >= p1RankPos) displayRank++;
        
        let isDecreed = !!imperialDecrees[item.id];
        let badgeClass = item.result === 'WIN' ? 'lose' : (item.result === 'LOSE' ? 'win' : 'draw');
        let badgeLabel = item.result === 'WIN' ? 'Derrota' : (item.result === 'LOSE' ? 'Vitória' : 'Empate');
        if (isDecreed) {
            badgeLabel = '👑 ' + (item.result === 'WIN' ? 'DERROTA' : 'VITÓRIA');
            badgeClass = item.result === 'WIN' ? 'lose' : 'win';
        }
        
        rankRows.push(`
            <tr onclick="loadBattleMatchup(${item.id})" class="${currentBattleOpponentId === item.id ? 'selected' : ''}">
                <td style="padding-left:10px; color:var(--text-muted);">${isDecreed ? '👑' : '#' + displayRank}</td>
                <td style="${isDecreed ? 'color:#fbbf24; font-weight:bold;' : ''}">${item.name}</td>
                <td style="text-align:center;"><span class="rinha-badge ${badgeClass}">${badgeLabel}</span></td>
                <td style="text-align:right; padding-right:10px; font-family:monospace; ${isDecreed ? 'color:#fbbf24;' : ''}">${item.score} pts</td>
            </tr>
        `);
    });
    
    if (p1RankPos >= items.length) {
        rankRows.push(`
            <tr class="selected" style="background: rgba(6, 182, 212, 0.15); border-left: 4px solid var(--cyan); font-weight: 700;">
                <td style="padding-left:10px; color:var(--cyan);">#101</td>
                <td>👑 ${p1GraphData.name} <span class="badge">CAMPEÃO</span></td>
                <td style="text-align:center;"><span class="rinha-badge win">P1</span></td>
                <td style="text-align:right; padding-right:10px; color:var(--cyan); font-family:monospace;">${p1Eval.score} pts</td>
            </tr>
        `);
    }
    
    tbody.innerHTML = rankRows.join('');
    showToast(`Rinha finalizada! Seu Grafo ficou em #${p1RankPos + 1} lugar de 101.`, 'success');
}

// Inicia Torneio Evolutivo (Desafios em cadeia)
function startEvolutionaryTournament() {
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Evoluindo...';
    badge.className = 'bot-status-tag';
    badge.style.borderColor = '#fbbf24';
    badge.style.color = '#fbbf24';
    
    const progressSection = document.getElementById('rinha-progress-section');
    const progressBar = document.getElementById('rinha-progress-bar');
    const progressLabel = document.getElementById('rinha-progress-label');
    const progressPercent = document.getElementById('rinha-progress-percent');
    
    progressSection.style.display = 'block';
    rinhaFights = [];
    
    let currentChampion = JSON.parse(JSON.stringify(p1GraphData));
    let round = 1;
    
    function processEvolutionRound() {
        let challenger;
        if (round === 1) {
            challenger = makeP1Procedural('random', 35);
            challenger.name = "Desafiante #1: Estrutura Inicial (ER)";
        } else {
            challenger = mutateGraph(currentChampion, round);
        }
        
        let p1Eval = evaluateGraphMetrics(currentChampion);
        let p2Eval = evaluateGraphMetrics(challenger);
        currentChampion.metrics = p1Eval;
        challenger.metrics = p2Eval;
        
        let res = 'DRAW';
        if (imperialDecrees[round]) {
            res = imperialDecrees[round] === 'P1' ? 'WIN' : 'LOSE';
        } else {
            if (p1Eval.score > p2Eval.score) res = 'WIN';
            else if (p1Eval.score < p2Eval.score) res = 'LOSE';
        }
        
        let roundWinner = res === 'LOSE' ? challenger : currentChampion;
        
        rinhaFights.push({
            round: round,
            champion: JSON.parse(JSON.stringify(currentChampion)),
            challenger: JSON.parse(JSON.stringify(challenger)),
            result: res,
            scoreP1: p1Eval.score,
            scoreP2: p2Eval.score,
            winnerName: roundWinner.name,
            mutation: challenger.name.split(':')[1]?.trim() || "Mutação de Estrutura Inicial"
        });
        
        currentChampion = JSON.parse(JSON.stringify(roundWinner));
        currentChampion.nodes.forEach(n => {
            n.x = undefined; n.y = undefined; n.fx = undefined; n.fy = undefined;
        });
        
        let pct = Math.round((round / 100) * 100);
        progressBar.style.width = pct + '%';
        progressPercent.textContent = pct + '%';
        progressLabel.textContent = `Rodada Evolutiva ${round} de 100...`;
        
        round++;
        if (round <= 100) {
            setTimeout(processEvolutionRound, 15);
        } else {
            finishEvolutionaryTournament();
        }
    }
    
    setTimeout(processEvolutionRound, 30);
}

// Renderiza a tabela do modo evolutivo
function finishEvolutionaryTournament() {
    const badge = document.getElementById('rinha-status-badge');
    badge.textContent = 'Evolução Concluída';
    badge.className = 'bot-status-tag status-online';
    
    const tbody = document.getElementById('rinha-rank-body');
    tbody.innerHTML = '';
    
    let rows = [];
    for (let i = rinhaFights.length - 1; i >= 0; i--) {
        let fight = rinhaFights[i];
        let isDecreed = !!imperialDecrees[fight.round];
        
        let badgeClass = fight.result === 'WIN' ? 'win' : (fight.result === 'LOSE' ? 'lose' : 'draw');
        let badgeLabel = fight.result === 'WIN' ? 'Defendeu' : (fight.result === 'LOSE' ? 'Destronado' : 'Empate');
        if (isDecreed) {
            badgeLabel = '👑 ' + (fight.result === 'WIN' ? 'DEFENDEU' : 'DESTRONADO');
            badgeClass = fight.result === 'WIN' ? 'win' : 'lose';
        }
        
        rows.push(`
            <tr onclick="loadEvolutionaryMatchup(${fight.round})" class="${currentBattleOpponentId === fight.round ? 'selected' : ''}">
                <td style="padding-left:10px; color:var(--text-muted);">${isDecreed ? '👑' : '#' + fight.round}</td>
                <td>
                    <div style="font-weight:bold; ${isDecreed ? 'color:#fbbf24;' : ''}">Luta ${fight.round}</div>
                    <div style="font-size:0.65rem; color:var(--text-muted);">${fight.challenger.name}</div>
                </td>
                <td style="text-align:center;"><span class="rinha-badge ${badgeClass}">${badgeLabel}</span></td>
                <td style="text-align:right; padding-right:10px; font-family:monospace; ${isDecreed ? 'color:#fbbf24;' : ''}">${fight.scoreP2} vs ${fight.scoreP1}</td>
            </tr>
        `);
    }
    
    tbody.innerHTML = rows.join('');
    showToast('Arena Evolutiva concluída com sucesso! Explore os rounds e decretos.', 'success');
}

// Carrega batalha evolutiva
function loadEvolutionaryMatchup(round) {
    const fight = rinhaFights.find(f => f.round === round);
    if (!fight) return;
    
    if (activeBattleInterval) clearInterval(activeBattleInterval);
    currentBattleOpponentId = round;
    
    document.getElementById('battle-versus-title').textContent = `Luta ${round}: Defensor VS Desafiante`;
    document.getElementById('battle-p1-name').textContent = fight.champion.name;
    document.getElementById('battle-p2-name').textContent = fight.challenger.name;
    
    const consoleEl = document.getElementById('arena-console');
    const p1Hubs = getSuperHubs(fight.champion);
    const oppHubs = getSuperHubs(fight.challenger);
    
    consoleEl.innerHTML = `> Iniciando Combate Evolutivo #${round}...<br>` +
        `> Mutação Utilizada: ${fight.mutation}<br>` +
        `> Defensor (P1): ${fight.champion.nodes.length} nós, Score: ${fight.scoreP1}<br>` +
        `> Desafiante (P2): ${fight.challenger.nodes.length} nós, Score: ${fight.scoreP2}`;
        
    const p1Container = document.getElementById('battle-canvas-p1');
    const p2Container = document.getElementById('battle-canvas-p2');
    
    p1Container.innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(6,182,212,0.15); color: var(--cyan); border: 1px solid rgba(6,182,212,0.3); padding: 2px 6px; border-radius: 4px;">P1: DEFENSOR</div>`;
    p2Container.innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); padding: 2px 6px; border-radius: 4px;">P2: DESAFIANTE</div>`;
    
    renderBattleGraph('battle-canvas-p1', fight.champion, 'cyan', p1Hubs);
    renderBattleGraph('battle-canvas-p2', fight.challenger, 'red', oppHubs);
    
    simulateFlowBattle(fight.champion, fight.challenger, p1Hubs, oppHubs);
}

// Mutação evolucionária baseada no vencedor anterior para derrotá-lo
function mutateGraph(baseGraph, round) {
    let copy = {
        id: round,
        name: `Desafiante #${round} (Evoluído)`,
        nodes: baseGraph.nodes.map(n => ({ id: n.id, label: n.label })),
        edges: baseGraph.edges.map(e => ({ source: e.source.id || e.source, target: e.target.id || e.target }))
    };
    
    let mutationName = "";
    let r = Math.random();
    
    if (r < 0.25) {
        let newHubId = "HubEvolutivo_" + round;
        copy.nodes.push({ id: newHubId, label: "SuperHub_Evolutivo" });
        let degMap = {};
        copy.nodes.forEach(n => degMap[n.id] = 0);
        copy.edges.forEach(e => {
            degMap[e.source] = (degMap[e.source] || 0) + 1;
            degMap[e.target] = (degMap[e.target] || 0) + 1;
        });
        let sorted = [...copy.nodes].sort((a,b) => (degMap[b.id]||0) - (degMap[a.id]||0));
        sorted.slice(0, 3).forEach(n => {
            if(n.id !== newHubId) copy.edges.push({ source: newHubId, target: n.id });
        });
        for(let j=0; j<4; j++) {
            let randNode = copy.nodes[Math.floor(Math.random() * (copy.nodes.length - 1))].id;
            if(randNode !== newHubId) copy.edges.push({ source: newHubId, target: randNode });
        }
        mutationName = "Módulo Super-Hub Adicionado";
    } else if (r < 0.5) {
        let superHubs = Array.from(getSuperHubs(copy));
        if(superHubs.length > 0) {
            let hubId = superHubs[Math.floor(Math.random() * superHubs.length)];
            let degMap = {};
            copy.nodes.forEach(n => degMap[n.id] = 0);
            copy.edges.forEach(e => {
                degMap[e.source] = (degMap[e.source] || 0) + 1;
                degMap[e.target] = (degMap[e.target] || 0) + 1;
            });
            let leaves = copy.nodes.filter(n => degMap[n.id] <= 2 && n.id !== hubId);
            let rewiredCount = 0;
            leaves.slice(0, 6).forEach(leaf => {
                copy.edges = copy.edges.filter(e => e.source !== leaf.id && e.target !== leaf.id);
                copy.edges.push({ source: leaf.id, target: hubId });
                rewiredCount++;
            });
            mutationName = `${rewiredCount} sub-nós acoplados ao Hub principal`;
        } else {
            copy.edges.push({ source: copy.nodes[0].id, target: copy.nodes[copy.nodes.length-1].id });
            mutationName = "Atração de Arestas";
        }
    } else if (r < 0.75) {
        let degMap = {};
        copy.nodes.forEach(n => degMap[n.id] = 0);
        copy.edges.forEach(e => {
            degMap[e.source] = (degMap[e.source] || 0) + 1;
            degMap[e.target] = (degMap[e.target] || 0) + 1;
        });
        let lowDeg = copy.nodes.filter(n => (degMap[n.id] || 0) === 0);
        let superHubs = Array.from(getSuperHubs(copy));
        if (lowDeg.length > 0 && superHubs.length > 0) {
            lowDeg.forEach(n => {
                let hub = superHubs[Math.floor(Math.random() * superHubs.length)];
                copy.edges.push({ source: n.id, target: hub });
            });
            mutationName = `${lowDeg.length} nós órfãos reintegrados a Módulos`;
        } else {
            let hubs = Array.from(getSuperHubs(copy));
            if(hubs.length > 1) {
                copy.edges.push({ source: hubs[0], target: hubs[1] });
                mutationName = "Cross-link entre Super-Hubs";
            } else {
                mutationName = "Reforço de Arestas Gerais";
            }
        }
    } else {
        let superHubs = Array.from(getSuperHubs(copy));
        if(superHubs.length > 0) {
            let hubId = superHubs[Math.floor(Math.random() * superHubs.length)];
            let neighbors = [];
            copy.edges.forEach(e => {
                let s = e.source.id || e.source;
                let t = e.target.id || e.target;
                if (s === hubId) neighbors.push(t);
                if (t === hubId) neighbors.push(s);
            });
            let cloneId = "HubClonado_" + round;
            copy.nodes.push({ id: cloneId, label: "ClonedHub" });
            copy.edges.push({ source: cloneId, target: hubId });
            neighbors.forEach(nId => {
                copy.edges.push({ source: cloneId, target: nId });
            });
            mutationName = "Super-Hub Clonado com Vizinhança";
        } else {
            mutationName = "Estabilização Modular";
        }
    }
    
    copy.name = `Desafiante #${round}: ${mutationName}`;
    return copy;
}

// Reseta a arena
function resetRinhaTournament() {
    if(activeBattleInterval) clearInterval(activeBattleInterval);
    imperialDecrees = {};
    currentBattleOpponentId = null;
    rinhaFights = [];
    document.getElementById('rinha-progress-section').style.display = 'none';
    document.getElementById('rinha-rank-body').innerHTML = `
        <tr>
            <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 40px 0;">Clique em "Iniciar Rinha Geral" para computar o ranking.</td>
        </tr>
    `;
    document.getElementById('battle-versus-title').textContent = `${p1GraphData ? p1GraphData.name : 'P1'} vs ...`;
    document.getElementById('battle-p1-score').textContent = '0';
    document.getElementById('battle-p2-score').textContent = '0';
    document.getElementById('battle-canvas-p1').innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(6,182,212,0.15); color: var(--cyan); border: 1px solid rgba(6,182,212,0.3); padding: 2px 6px; border-radius: 4px;">P1: DESAFIANTE</div>`;
    document.getElementById('battle-canvas-p2').innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); padding: 2px 6px; border-radius: 4px;">P2: OPONENTE</div>`;
    document.getElementById('arena-console').innerHTML = `> Selecione um oponente no ranking para assistir à simulação de combate.`;
}

// Decreto do Imperador
function emperorDecree(winner) {
    if (!currentBattleOpponentId) {
        showToast('Selecione uma batalha no ranking antes de decretar o vencedor!', 'error');
        return;
    }
    
    if (activeBattleInterval) clearInterval(activeBattleInterval);
    
    imperialDecrees[currentBattleOpponentId] = winner;
    
    const consoleEl = document.getElementById('arena-console');
    const p1ScoreEl = document.getElementById('battle-p1-score');
    const p2ScoreEl = document.getElementById('battle-p2-score');
    
    if (winner === 'P1') {
        p1ScoreEl.textContent = '100%';
        p2ScoreEl.textContent = '0%';
        d3.selectAll('#battle-canvas-p1 .arena-node').style('fill', 'var(--cyan)').style('filter', 'url(#glow-battle-canvas-p1)').attr('r', 8);
        d3.selectAll('#battle-canvas-p2 .arena-node').style('fill', 'rgba(255,255,255,0.05)').style('filter', 'none').attr('r', 3);
        consoleEl.innerHTML = `<span style="color:#fbbf24; font-weight:bold;">> 👑 DECRETO IMPERIAL: Sua Majestade Imperial decretou a vitória incondicional de P1 (Campeão)!</span><br>` + consoleEl.innerHTML;
        showToast('Decreto Real Aplicado! Vitória de P1.', 'success');
    } else {
        p1ScoreEl.textContent = '0%';
        p2ScoreEl.textContent = '100%';
        d3.selectAll('#battle-canvas-p1 .arena-node').style('fill', 'rgba(255,255,255,0.05)').style('filter', 'none').attr('r', 3);
        d3.selectAll('#battle-canvas-p2 .arena-node').style('fill', 'var(--red)').style('filter', 'url(#glow-battle-canvas-p2)').attr('r', 8);
        consoleEl.innerHTML = `<span style="color:#fbbf24; font-weight:bold;">> 👑 DECRETO IMPERIAL: Sua Majestade Imperial decretou a vitória incondicional do Desafiante (P2)!</span><br>` + consoleEl.innerHTML;
        showToast('Decreto Real Aplicado! Vitória de P2.', 'error');
    }
    
    if (rinhaMode === 'evolutionary') {
        startEvolutionaryTournament();
    } else {
        startClassicTournament();
    }
}

// Carrega batalha clássica individual no visualizador
function loadBattleMatchup(opponentId) {
    const opp = rinhaOpponents.find(o => o.id === opponentId);
    if (!opp) return;
    
    currentBattleOpponentId = opponentId;
    if (activeBattleInterval) clearInterval(activeBattleInterval);
    
    document.getElementById('battle-versus-title').textContent = `${p1GraphData.name.replace('Seu ', '')} VS ${opp.name.split(':')[1].trim()}`;
    document.getElementById('battle-p1-name').textContent = p1GraphData.name;
    document.getElementById('battle-p2-name').textContent = opp.name;
    
    const consoleEl = document.getElementById('arena-console');
    const p1Hubs = getSuperHubs(p1GraphData);
    const oppHubs = getSuperHubs(opp);
    
    consoleEl.innerHTML = `> Iniciando combate...<br>` +
        `> P1 Super-Hubs identificados: ${p1Hubs.size} nós estratégicos.<br>` +
        `> P2 Super-Hubs identificados: ${oppHubs.size} nós estratégicos.<br>` +
        `> Avaliação baseada na capacidade de agrupar sub-nós ao redor destes super-hubs.`;
    
    const p1Container = document.getElementById('battle-canvas-p1');
    const p2Container = document.getElementById('battle-canvas-p2');
    
    p1Container.innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(6,182,212,0.15); color: var(--cyan); border: 1px solid rgba(6,182,212,0.3); padding: 2px 6px; border-radius: 4px;">P1: DESAFIANTE</div>`;
    p2Container.innerHTML = `<div class="canvas-label" style="position: absolute; top: 10px; left: 10px; font-size: 0.6rem; font-weight: 800; background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); padding: 2px 6px; border-radius: 4px;">P2: OPONENTE</div>`;
    
    renderBattleGraph('battle-canvas-p1', p1GraphData, 'cyan', p1Hubs);
    renderBattleGraph('battle-canvas-p2', opp, 'red', oppHubs);
    
    simulateFlowBattle(p1GraphData, opp, p1Hubs, oppHubs);
}

// Renderiza D3 em container (desenhando nomes em todos os nós e identificando hubs)
function renderBattleGraph(containerId, graph, colorTheme, hubs) {
    const container = document.getElementById(containerId);
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    const svg = d3.select('#' + containerId).append('svg')
        .attr('width', width)
        .attr('height', height);
        
    const g = svg.append('g');
    
    const color = colorTheme === 'cyan' ? 'var(--cyan)' : 'var(--red)';
    const glowId = 'glow-' + containerId;
    
    const defs = svg.append('defs');
    const filter = defs.append('filter').attr('id', glowId)
        .attr('x', '-60%').attr('y', '-60%').attr('width', '220%').attr('height', '220%');
    filter.append('feDropShadow').attr('dx', 0).attr('dy', 0).attr('stdDeviation', 4)
        .attr('flood-color', color);
        
    const sim = d3.forceSimulation(graph.nodes)
        .force('link', d3.forceLink(graph.edges).id(d => d.id).distance(50).strength(0.85))
        .force('charge', d3.forceManyBody().strength(-60))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => hubs.has(d.id) ? 14 : 9));
        
    const link = g.selectAll('.arena-link')
        .data(graph.edges)
        .enter().append('line')
        .attr('class', 'arena-link')
        .style('stroke', 'rgba(255,255,255,0.12)');
        
    const node = g.selectAll('.arena-node')
        .data(graph.nodes)
        .enter().append('circle')
        .attr('class', 'arena-node')
        .attr('id', `node-${containerId}-${graph.id}`)
        .attr('r', d => hubs.has(d.id) ? 9 : 4.5)
        .style('fill', 'rgba(255,255,255,0.25)')
        .style('stroke', d => hubs.has(d.id) ? '#fbbf24' : color) // Hubs em dourado
        .style('stroke-width', d => hubs.has(d.id) ? '3px' : '1.5px');
        
    // Adiciona o nome em todos os nós
    const text = g.selectAll('.arena-text')
        .data(graph.nodes)
        .enter().append('text')
        .attr('class', 'arena-text')
        .attr('dx', d => hubs.has(d.id) ? 12 : 8)
        .attr('dy', 3)
        .style('font-size', d => hubs.has(d.id) ? '9px' : '6.5px')
        .style('font-weight', d => hubs.has(d.id) ? 'bold' : 'normal')
        .style('fill', d => hubs.has(d.id) ? '#fff' : '#94a3b8')
        .style('pointer-events', 'none')
        .text(d => d.label);
        
    sim.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
            
        node
            .attr('cx', d => d.x = Math.max(12, Math.min(width - 12, d.x)))
            .attr('cy', d => d.y = Math.max(12, Math.min(height - 12, d.y)));
            
        text
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    if (containerId === 'battle-canvas-p1') {
        currentBattleSimP1 = { nodes: graph.nodes, edges: graph.edges, d3: sim, element: node };
    } else {
        currentBattleSimP2 = { nodes: graph.nodes, edges: graph.edges, d3: sim, element: node };
    }
}

// Simula fluxo (começando a partir dos super-hubs)
function simulateFlowBattle(p1, p2, p1Hubs, p2Hubs) {
    let p1Active = new Set();
    let p2Active = new Set();
    
    p1Hubs.forEach(hId => p1Active.add(hId));
    p2Hubs.forEach(hId => p2Active.add(hId));
    
    const consoleEl = document.getElementById('arena-console');
    const p1ScoreEl = document.getElementById('battle-p1-score');
    const p2ScoreEl = document.getElementById('battle-p2-score');
    
    let ticks = 0;
    
    const buildAdj = (edges) => {
        let adj = {};
        edges.forEach(e => {
            let s = e.source.id || e.source;
            let t = e.target.id || e.target;
            if(!adj[s]) adj[s] = [];
            if(!adj[t]) adj[t] = [];
            adj[s].push(t);
            adj[t].push(s);
        });
        return adj;
    };
    
    const p1Adj = buildAdj(p1.edges);
    const p2Adj = buildAdj(p2.edges);
    
    activeBattleInterval = setInterval(() => {
        ticks++;
        
        let p1Next = new Set(p1Active);
        p1Active.forEach(nodeId => {
            let neigh = p1Adj[nodeId] || [];
            neigh.forEach(n => p1Next.add(n));
        });
        
        let p2Next = new Set(p2Active);
        p2Active.forEach(nodeId => {
            let neigh = p2Adj[nodeId] || [];
            neigh.forEach(n => p2Next.add(n));
        });
        
        p1Active = p1Next;
        p2Active = p2Next;
        
        // Atualiza preenchimento nos canvases
        d3.selectAll('#battle-canvas-p1 .arena-node')
            .style('fill', d => p1Active.has(d.id) ? (p1Hubs.has(d.id) ? '#fbbf24' : 'var(--cyan)') : 'rgba(255,255,255,0.25)')
            .style('filter', d => p1Active.has(d.id) ? 'url(#glow-battle-canvas-p1)' : 'none')
            .attr('r', d => p1Active.has(d.id) ? (p1Hubs.has(d.id) ? 11 : 6) : (p1Hubs.has(d.id) ? 9 : 4.5));
            
        d3.selectAll('#battle-canvas-p2 .arena-node')
            .style('fill', d => p2Active.has(d.id) ? (p2Hubs.has(d.id) ? '#fbbf24' : 'var(--red)') : 'rgba(255,255,255,0.25)')
            .style('filter', d => p2Active.has(d.id) ? 'url(#glow-battle-canvas-p2)' : 'none')
            .attr('r', d => p2Active.has(d.id) ? (p2Hubs.has(d.id) ? 11 : 6) : (p2Hubs.has(d.id) ? 9 : 4.5));
            
        let p1Pct = p1.nodes.length > 0 ? Math.round((p1Active.size / p1.nodes.length) * 100) : 0;
        let p2Pct = p2.nodes.length > 0 ? Math.round((p2Active.size / p2.nodes.length) * 100) : 0;
        
        p1ScoreEl.textContent = p1Pct + '%';
        p2ScoreEl.textContent = p2Pct + '%';
        
        if(ticks % 2 === 0) {
            consoleEl.innerHTML = `> [Tick ${ticks}] Transmitindo dados a partir dos Super-Hubs...<br>` +
                `> P1 Agrupado: ${p1Pct}% (${p1Active.size}/${p1.nodes.length} nós acoplados)<br>` +
                `> P2 Agrupado: ${p2Pct}% (${p2Active.size}/${p2.nodes.length} nós acoplados)<br>` +
                consoleEl.innerHTML.split('<br>').slice(0, 3).join('<br>');
        }
        
        let doneP1 = p1Pct >= 100 || p1Active.size === p1.nodes.length;
        let doneP2 = p2Pct >= 100 || p2Active.size === p2.nodes.length;
        
        if ((doneP1 && doneP2) || ticks >= 45) {
            clearInterval(activeBattleInterval);
            let winner = 'Empate';
            if (p1Pct > p2Pct) {
                winner = p1GraphData.name;
                consoleEl.innerHTML = `<span style="color:var(--cyan); font-weight:bold;">> VITÓRIA DO DESAFIANTE por maior capacidade de agrupamento e disseminação a partir dos hubs!</span><br>` + consoleEl.innerHTML;
                showToast('Vitória do P1!', 'info');
            } else if (p2Pct > p1Pct) {
                winner = p2.name;
                consoleEl.innerHTML = `<span style="color:var(--red); font-weight:bold;">> VITÓRIA DO OPONENTE por melhor acoplamento modular e estrutura de hubs!</span><br>` + consoleEl.innerHTML;
                showToast('Vitória do P2!', 'error');
            } else {
                consoleEl.innerHTML = `<span style="color:var(--amber); font-weight:bold;">> EMPATE TÉCNICO! Ambas as topologias possuem o mesmo coeficiente de agrupamento modular.</span><br>` + consoleEl.innerHTML;
                showToast('Empate técnico!', 'info');
            }
        }
    }, 220);
}

// ============================================================
// SISTEMA DE KANBAN DE MELHORIAS (10k)
// ============================================================
let currentKanbanData = [];

async function loadKanban() {
    const q = document.getElementById('kanban-search').value;
    const cat = document.getElementById('kanban-category').value;
    
    // Mostra loaders simples
    document.getElementById('kb-col-todo').innerHTML = '<p style="color:var(--text-muted); padding:10px; font-size:0.75rem;">Carregando...</p>';
    document.getElementById('kb-col-progress').innerHTML = '<p style="color:var(--text-muted); padding:10px; font-size:0.75rem;">Carregando...</p>';
    document.getElementById('kb-col-done').innerHTML = '<p style="color:var(--text-muted); padding:10px; font-size:0.75rem;">Carregando...</p>';
    
    try {
        const url = `/api/improvements?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}`;
        const r = await fetch(url);
        const data = await r.json();
        
        // Armazena dados no cache global local
        currentKanbanData = [...data.todo, ...data.in_progress, ...data.done];
        
        // Atualiza stats
        document.getElementById('kb-stat-total').textContent = data.stats.total;
        document.getElementById('kb-stat-todo').textContent = data.stats.todo;
        document.getElementById('kb-stat-progress').textContent = data.stats.in_progress;
        document.getElementById('kb-stat-done').textContent = data.stats.done;
        
        document.getElementById('kb-count-todo').textContent = data.stats.todo;
        document.getElementById('kb-count-progress').textContent = data.stats.in_progress;
        document.getElementById('kb-count-done').textContent = data.stats.done;
        
        // Renderiza colunas
        renderKanbanColumn('kb-col-todo', data.todo, 'todo');
        renderKanbanColumn('kb-col-progress', data.in_progress, 'in_progress');
        renderKanbanColumn('kb-col-done', data.done, 'done');
        
    } catch(e) {
        console.error("Erro ao carregar o Kanban:", e);
        showToast("Erro ao carregar o Kanban", "error");
    }
}

function renderKanbanColumn(containerId, items, columnStatus) {
    const col = document.getElementById(containerId);
    if (!items || items.length === 0) {
        col.innerHTML = '<p style="color:var(--text-muted); font-size:0.75rem; text-align:center; padding:30px 0;">Vazio</p>';
        return;
    }
    
    col.innerHTML = items.map(item => {
        let actionBtn = '';
        if (columnStatus === 'todo') {
            actionBtn = `<button class="btn" style="padding:4px 8px; font-size:0.6rem; border-color:var(--cyan); color:var(--cyan); margin-top:8px;" onclick="event.stopPropagation(); moveImprovement('${item.id}', 'in_progress')">⚡ Iniciar</button>`;
        } else if (columnStatus === 'in_progress') {
            actionBtn = `<button class="btn" style="padding:4px 8px; font-size:0.6rem; border-color:var(--green); color:var(--green); margin-top:8px;" onclick="event.stopPropagation(); moveImprovement('${item.id}', 'done')">✓ Concluir</button>`;
        }
        
        let difficultyColor = 'var(--green)';
        if (item.difficulty === 'medium') difficultyColor = 'var(--amber)';
        if (item.difficulty === 'hard') difficultyColor = 'var(--red)';
        
        let priorityColor = 'var(--text-muted)';
        if (item.priority === 'high') priorityColor = 'var(--red)';
        if (item.priority === 'medium') priorityColor = 'var(--amber)';
        if (item.priority === 'low') priorityColor = 'var(--cyan)';
        
        return `
            <div class="card" onclick="openKanbanDetail('${item.id}', event)" style="padding:15px; margin-bottom:0; cursor:pointer; border-left:3px solid ${
                item.category === 'Performance' ? 'var(--cyan)' :
                item.category === 'RAG' ? 'var(--green)' :
                item.category === 'UI/UX' ? 'var(--accent)' : 'var(--text-muted)'
            }; background: rgba(15, 23, 42, 0.6); display: flex; flex-direction: column; gap: 8px;">
                <div style="display:flex; justify-content:space-between; font-size:0.6rem; color:var(--text-muted); align-items:center;">
                    <span style="font-weight:700; color:white;">${item.id}</span>
                    <div style="display:flex; gap:4px;">
                        <span class="badge" style="font-size:0.55rem; color:${difficultyColor}; border-color:${difficultyColor}33; background:${difficultyColor}11;">${item.difficulty.toUpperCase()}</span>
                        <span class="badge" style="font-size:0.55rem; color:${priorityColor}; border-color:${priorityColor}33; background:${priorityColor}11;">${(item.priority || 'medium').toUpperCase()}</span>
                    </div>
                </div>
                <h4 style="margin:0; font-size:0.8rem; font-family:'Outfit'; color:#fff; font-weight: 600;">${item.title.split(': ').slice(1).join(': ') || item.title}</h4>
                <p style="margin:0; font-size:0.7rem; color:var(--text-muted); line-height:1.4; display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">${item.description}</p>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px; border-top:1px solid rgba(255,255,255,0.03); padding-top:8px;">
                    <span class="badge" style="font-size:0.55rem;">${item.category}</span>
                    ${actionBtn}
                </div>
            </div>
        `;
    }).join('');
}

function openKanbanDetail(itemId, event) {
    if (event && event.target.closest('button')) return;
    
    const item = currentKanbanData.find(i => i.id === itemId);
    if (!item) return;
    
    const panel   = document.getElementById('node-panel');
    const content = document.getElementById('node-panel-content');
    
    let difficultyColor = 'var(--green)';
    if (item.difficulty === 'medium') difficultyColor = 'var(--amber)';
    if (item.difficulty === 'hard') difficultyColor = 'var(--red)';
    
    let priorityColor = 'var(--text-muted)';
    if (item.priority === 'high') priorityColor = 'var(--red)';
    if (item.priority === 'medium') priorityColor = 'var(--amber)';
    if (item.priority === 'low') priorityColor = 'var(--cyan)';
    
    content.innerHTML = `
        <h2 style="font-family:'Outfit';font-size:1.5rem;font-weight:800;color:white;margin-top:0;margin-bottom:5px;">${item.title.split(': ').slice(1).join(': ') || item.title}</h2>
        <p style="color:var(--cyan);font-weight:700;font-size:0.72rem;letter-spacing:1.5px;text-transform:uppercase;margin-top:0;margin-bottom:20px;">Melhoria • ${item.category}</p>
        
        <div style="display:flex; gap:10px; margin-bottom:25px;">
            <span class="badge" style="color:${difficultyColor}; border-color:${difficultyColor}33; background:${difficultyColor}11; padding:4px 8px;">DIFICULDADE: ${item.difficulty.toUpperCase()}</span>
            <span class="badge" style="color:${priorityColor}; border-color:${priorityColor}33; background:${priorityColor}11; padding:4px 8px;">PRIORIDADE: ${(item.priority || 'medium').toUpperCase()}</span>
        </div>

        <div style="margin-bottom:22px; border-top:1px solid var(--border); padding-top:18px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">Identificador</h4>
            <div style="font-family:monospace;font-size:0.82rem;color:#fff;background:rgba(0,0,0,0.25);padding:10px 14px;border-radius:10px;word-break:break-all;border:1px solid var(--border);">${item.id}</div>
        </div>

        <div style="margin-bottom:22px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">O que será ajustado</h4>
            <p style="font-size:0.85rem; color:#fff; line-height:1.6; margin:0; background:rgba(255,255,255,0.02); padding:12px; border-radius:10px; border:1px solid var(--border);">${item.details || item.description}</p>
        </div>

        <div style="margin-bottom:22px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">Motivos & Justificativas</h4>
            <p style="font-size:0.85rem; color:#94a3b8; line-height:1.6; margin:0; background:rgba(255,255,255,0.02); padding:12px; border-radius:10px; border:1px solid var(--border);">${item.motivation_justification || 'Não fornecido.'}</p>
        </div>

        <div style="margin-bottom:22px;">
            <h4 style="margin:0 0 10px 0;font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:1.5px;">Status Atual</h4>
            <span class="badge" style="padding:4px 8px; font-weight:800; text-transform:uppercase; ${
                item.status === 'done' ? 'color:var(--green); border-color:rgba(16,185,129,0.3); background:rgba(16,185,129,0.1);' :
                item.status === 'in_progress' ? 'color:var(--cyan); border-color:rgba(6,182,212,0.3); background:rgba(6,182,212,0.1);' :
                'color:var(--text-muted); border-color:var(--border);'
            }">${item.status === 'in_progress' ? 'EM PROGRESSO' : item.status === 'done' ? 'CONCLUÍDO' : 'A FAZER'}</span>
            ${item.completed_at ? `<p style="font-size:0.7rem; color:var(--text-muted); margin-top:8px;">Concluído em: ${item.completed_at.replace('T', ' ').slice(0, 16)}</p>` : ''}
        </div>
    `;
    
    panel.classList.add('open');
}

async function moveImprovement(id, newStatus) {
    const d = await apiCall('/api/improvements/move', 'POST', { id, status: newStatus });
    if (d && d.status === 'ok') {
        loadKanban();
    }
}

async function applyDailyImprovements(btn) {
    const d = await apiCall('/api/improvements/apply-daily', 'POST', {}, btn);
    if (d && d.status === 'ok') {
        loadKanban();
        if (d.applied) {
            d.applied.forEach(item => {
                showToast(`Melhoria aplicada: ${item.id}`, 'success');
            });
        }
    }
}

let isOfficeAnimating = false;

function renderDevs(count, devStatus) {
    const container = document.getElementById('dev-avatars-container');
    if (!container) return;
    
    let html = '';
    const width = 38;
    const spacing = 44;
    const devEmojis = ['👨‍💻', '👩‍💻', '💻', '🖥️', '⌨️', '⚙️', '🛠️', '🔌', '💾', '💿'];
    // Devs ficam alinhados da esquerda para a direita dentro do container
    for (let i = 0; i < count; i++) {
        const leftPx = i * spacing;
        const emoji = devEmojis[i % devEmojis.length];
        const name = `Dev-${i + 1}`;
        const isLead = i === 0;
        const glowColor = isLead ? '6,182,212' : '56,189,248';
        html += `
            <div class="avatar dev-avatar" id="avatar-dev-${i}" style="position: absolute; bottom: 5px; left: ${leftPx}px; width: ${width}px; height: ${width}px; border-radius: 50%; background: #06b6d4; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; transition: all 1.2s ease-in-out; z-index: 10; box-shadow: 0 0 10px rgba(${glowColor},0.4); border: 2px solid white; cursor: pointer;" data-tooltip="${name} ${isLead ? '(Lead)' : ''}">
                ${emoji}
            </div>
        `;
    }
    container.innerHTML = html;
}

async function hireDev() {
    try {
        const r = await fetch('/api/office/hire', { method: 'POST' });
        const res = await r.json();
        if (res.status === 'ok') {
            loadOfficeData();
            showToast(`Novo Dev Contratado! Equipe expandida para ${res.dev_count}.`, 'success');
        }
    } catch(e) {
        console.error("Erro ao contratar dev:", e);
    }
}

async function fireDev() {
    try {
        const r = await fetch('/api/office/fire', { method: 'POST' });
        const res = await r.json();
        if (res.status === 'ok') {
            loadOfficeData();
            showToast(`Dev demitido. Equipe reduzida para ${res.dev_count}.`, 'info');
        }
    } catch(e) {
        console.error("Erro ao demitir dev:", e);
    }
}

async function loadOfficeData() {
    try {
        const r = await fetch('/api/office');
        const data = await r.json();
        
        // 1. Atualiza status do Dev
        const devStatusTag = document.getElementById('dev-work-status');
        const devConsoleText = document.getElementById('dev-console-text');
        
        // Atualiza contagem de devs contratados no painel
        const devCountVal = data.dev_count || 1;
        document.getElementById('dev-hired-count').innerText = devCountVal;
        
        if (data.dev_status === 'WORKING') {
            devStatusTag.className = 'bot-status-tag status-online';
            devStatusTag.innerHTML = `<div class="status-dot"></div> CODANDO (${devCountVal} DEVS)`;
            devConsoleText.innerHTML = `> Analisando ${devCountVal * 3} melhorias em paralelo...\n> Rodando pytest unit tests...\n> Executando git commit & push...`;
            devStatusTag.style.background = 'rgba(6,182,212,0.1)';
            devStatusTag.style.color = 'var(--cyan)';
        } else {
            devStatusTag.className = 'bot-status-tag status-offline';
            devStatusTag.innerHTML = '<div class="status-dot" style="background:#64748b;"></div> OCIOSO';
            devStatusTag.style.background = 'rgba(100,116,139,0.1)';
            devStatusTag.style.color = '#64748b';
            devConsoleText.innerHTML = `> Monitorando backlog...\n> ${devCountVal} Devs contratados aguardando novas reclamações.`;
        }
        
        // Renderiza visualmente os desenvolvedores na estação
        renderDevs(devCountVal, data.dev_status);
        
        // 2. Renderiza logs do Cliente Oculto
        const mysteryContainer = document.getElementById('mystery-logs-container');
        if (data.mystery_logs && data.mystery_logs.length > 0) {
            mysteryContainer.innerHTML = data.mystery_logs.map(log => `<div>> ${log}</div>`).join('');
        } else {
            mysteryContainer.innerHTML = '<div>> Nenhuma refatoração silenciosa aplicada ainda.</div>';
        }
        
        // 3. Renderiza tabela do Usuário Chato
        const feedbackBody = document.getElementById('office-feedback-table-body');
        if (data.feedbacks && data.feedbacks.length > 0) {
            feedbackBody.innerHTML = data.feedbacks.reverse().map(fb => {
                let badgeClass = 'badge';
                let badgeStyle = 'background: rgba(100,116,139,0.1); border-color: rgba(100,116,139,0.2); color: #64748b;';
                let decisionText = 'PENDENTE';
                
                if (fb.status === 'accepted') {
                    badgeStyle = 'background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.2); color: var(--green);';
                    decisionText = 'ACEITO (KBCard)';
                } else if (fb.status === 'duplicate') {
                    badgeStyle = 'background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.2); color: var(--red);';
                    decisionText = 'REJEITADO (Duplicado)';
                } else if (fb.status === 'failed') {
                    badgeStyle = 'background: rgba(251,191,36,0.1); border-color: rgba(251,191,36,0.2); color: var(--amber);';
                    decisionText = 'ERRO';
                }
                
                const timeStr = fb.timestamp ? new Date(fb.timestamp).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'}) : '...';
                
                return `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <td style="padding: 12px; color: var(--text-muted); padding-left: 15px;">${timeStr}</td>
                        <td style="padding: 12px; color: #f1f5f9;">
                            <div style="font-weight: 700; color: var(--cyan); margin-bottom: 4px; font-size: 0.75rem;">
                                ${fb.avatar || '🤬'} ${fb.user || 'Usuário Chato'} <span style="font-weight: 400; color: var(--text-muted); font-size: 0.65rem;">(${fb.role || 'Testador'})</span>
                            </div>
                            <div style="font-weight: 500;">"${fb.complaint}"</div>
                        </td>
                        <td style="padding: 12px; text-align: right; padding-right: 15px;">
                            <span class="${badgeClass}" style="${badgeStyle}">${decisionText}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            feedbackBody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 30px;">Nenhuma reclamação ou feedback catalogado ainda.</td></tr>';
        }

        // 4. Dispara animação completa do pipeline na mapa do escritório
        if (!isOfficeAnimating && data.feedbacks && data.feedbacks.length > 0) {
            const last = data.feedbacks[data.feedbacks.length - 1];
            triggerOfficeAnimation(last);
        }

        // 5. Renderiza Ranking de Usuários
        if (data.ranking) renderRanking(data.ranking);

        // 6. Renderiza KPIs de Atendimento TI
        if (data.ranking) renderKPIs(data.ranking);
        
    } catch(e) {
        console.error("Erro ao carregar dados do escritório virtual:", e);
    }
}

function renderRanking(ranking) {
    const container = document.getElementById('ranking-list');
    if (!container) return;
    container.style.maxHeight = '360px';
    container.style.overflowY  = 'auto';

    const GOAL = 10_000;
    const medals = ['🥇','🥈','🥉'];

    if (!ranking || ranking.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:20px;">Nenhum usuário ainda. Aguardando feedbacks...</div>';
        return;
    }

    container.innerHTML = ranking.map((p, i) => {
        const pct      = p.pct_goal ?? 0;
        const accepted = p.accepted ?? 0;
        const goal     = p.goal     ?? GOAL;
        const won      = p.won      ?? false;

        const barColor = won
            ? 'linear-gradient(90deg,#10b981,#34d399)'
            : pct >= 50  ? 'linear-gradient(90deg,#06b6d4,#818cf8)'
            : pct >= 20  ? 'linear-gradient(90deg,#f59e0b,#fb923c)'
            :               'linear-gradient(90deg,#ef4444,#f87171)';

        const rateColor = p.acceptance_rate >= 80 ? '#10b981'
                        : p.acceptance_rate >= 50 ? '#f59e0b' : '#ef4444';

        const medal = won ? '🏆' : (medals[i] ?? `<span style="font-size:0.72rem;color:var(--text-muted);">#${i+1}</span>`);
        const areaBadge = p.area
            ? `<span style="font-size:0.55rem;background:rgba(6,182,212,0.12);color:var(--cyan);border:1px solid rgba(6,182,212,0.25);border-radius:4px;padding:1px 5px;">${p.area}</span>`
            : '';
        const wonBadge  = won
            ? '<span style="font-size:0.6rem;background:rgba(251,191,36,0.15);color:#fbbf24;border:1px solid rgba(251,191,36,0.3);border-radius:4px;padding:1px 6px;font-weight:800;">🏆 CAMPEÃO</span>'
            : '';

        return `
        <div style="display:flex;flex-direction:column;gap:5px;padding:9px 12px;border-radius:10px;
                    background:${won ? 'rgba(251,191,36,0.06)' : 'rgba(255,255,255,0.025)'};
                    border:1px solid ${won ? 'rgba(251,191,36,0.25)' : 'rgba(255,255,255,0.06)'};">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
                <span style="display:flex;align-items:center;gap:6px;flex:1;min-width:0;font-size:0.82rem;font-weight:700;">
                    <span style="font-size:1rem;flex-shrink:0;">${medal}</span>
                    <span style="font-size:0.95rem;flex-shrink:0;">${p.emoji}</span>
                    <span style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.name}</span>
                    ${areaBadge}${wonBadge}
                    <span style="font-size:0.6rem;font-weight:400;color:var(--text-muted);flex-shrink:0;">${p.role}</span>
                </span>
                <span style="font-size:0.68rem;font-weight:800;color:${rateColor};white-space:nowrap;">
                    ${accepted.toLocaleString('pt-BR')}/${goal.toLocaleString('pt-BR')}
                </span>
            </div>
            <!-- Barra de progresso até 10K -->
            <div style="background:rgba(255,255,255,0.06);border-radius:6px;height:6px;overflow:hidden;">
                <div style="width:${pct}%;height:100%;background:${barColor};border-radius:6px;transition:width 0.8s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.6rem;color:var(--text-muted);">
                <span>Taxa aceite: <b style="color:${rateColor};">${p.acceptance_rate}%</b></span>
                <span>${pct.toFixed(2)}% da meta de 10K${won ? ' ✅' : ''}</span>
            </div>
        </div>`;
    }).join('');
}

function renderKPIs(ranking) {
    const container = document.getElementById('kpi-list');
    if (!container) return;
    container.style.maxHeight = '360px';
    container.style.overflowY  = 'auto';

    if (!ranking || ranking.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted);font-size:0.8rem;text-align:center;padding:20px;">Aguardando dados...</div>';
        return;
    }

    const palette = ['#f59e0b','#06b6d4','#a855f7','#ec4899','#10b981','#f97316','#8b5cf6','#0ea5e9','#14b8a6','#e11d48'];
    container.innerHTML = ranking.map((p, i) => {
        const rateColor = p.acceptance_rate >= 80 ? '#10b981' : p.acceptance_rate >= 50 ? '#f59e0b' : '#ef4444';
        const color = palette[i % palette.length];
        return `
        <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;
                    background:rgba(255,255,255,0.025);border-left:3px solid ${color};
                    border-top:1px solid rgba(255,255,255,0.04);border-right:1px solid rgba(255,255,255,0.04);border-bottom:1px solid rgba(255,255,255,0.04);">
            <span style="font-size:1.15rem;min-width:24px;text-align:center;">${p.emoji}</span>
            <div style="flex:1;min-width:0;">
                <div style="font-size:0.78rem;font-weight:700;color:white;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${p.name}</div>
                <div style="font-size:0.6rem;color:var(--text-muted);">${p.role}${p.area?' • '+p.area:''} • hoje: <b style="color:white;">${p.today}</b></div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;min-width:100px;">
                <div style="font-size:0.6rem;color:#10b981;">✅ <b>${(p.accepted||0).toLocaleString('pt-BR')}</b> aceitos</div>
                <div style="font-size:0.6rem;color:#64748b;">🔄 <b>${p.duplicate||0}</b> duplic.</div>
                <div style="font-size:0.62rem;color:${rateColor};font-weight:800;">Taxa ${p.acceptance_rate}%</div>
            </div>
        </div>`;
    }).join('');
}

async function hirePM() {
    try {
        const r   = await fetch('/api/office/hire-pm', { method: 'POST' });
        const res = await r.json();
        if (res.status === 'ok') {
            loadOfficeData();
            showToast(`Novo PM contratado! Equipe: ${res.pm_count} PMs.`, 'success');
        }
    } catch(e) { console.error(e); }
}

async function firePM() {
    try {
        const r   = await fetch('/api/office/fire-pm', { method: 'POST' });
        const res = await r.json();
        if (res.status === 'ok') {
            loadOfficeData();
            showToast(`PM demitido. Equipe: ${res.pm_count} PMs.`, 'info');
        }
    } catch(e) { console.error(e); }
}

function renderPMs(pmCount) {
    const container = document.getElementById('pm-avatars-container');
    if (!container) return;
    const emojis = ['📋','🗂️','📌','📊','📝'];
    let html = '';
    for (let i = 0; i < pmCount; i++) {
        html += `<div class="avatar" id="avatar-pm-${i}" style="position:absolute;top:5px;left:${i*42}px;width:34px;height:34px;border-radius:50%;background:#a855f7;display:flex;align-items:center;justify-content:center;font-size:1rem;box-shadow:0 0 8px rgba(168,85,247,0.4);border:2px solid white;cursor:pointer;z-index:10;" data-tooltip="PM-${i+1}">${emojis[i % emojis.length]}</div>`;
    }
    container.innerHTML = html;
    // Atualiza o avatar principal do mapa (avatar-pm) para o primeiro
    const mainPM = document.getElementById('avatar-pm');
    if (mainPM) mainPM.innerHTML = emojis[0];
}

function showBubble(id, text, timeout = 3000) {
    const bubble = document.getElementById(id);
    if (!bubble) return;
    bubble.innerHTML = text;
    bubble.style.display = 'block';
    setTimeout(() => {
        bubble.style.display = 'none';
    }, timeout);
}

function moveAvatar(id, props, delay = 0) {
    return new Promise(resolve => {
        setTimeout(() => {
            const el = document.getElementById(id);
            if (el) Object.assign(el.style, props);
            setTimeout(resolve, 1300); // Wait for CSS transition to finish
        }, delay);
    });
}

function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Full pipeline state machine:
// User → PM → Dev → QA → (fail: QA→Dev loop) → (pass: QA→User approval) → done or back to backlog
async function triggerOfficeAnimation(latestFeedback) {
    if (isOfficeAnimating) return;
    isOfficeAnimating = true;

    const qa = document.getElementById('avatar-qa');
    const user = document.getElementById('avatar-user');
    const pm = document.getElementById('avatar-pm');

    if (!user || !pm) { isOfficeAnimating = false; return; }

    // ── RESET positions ────────────────────────────────────
    const devCount = document.querySelectorAll('.dev-avatar').length || 1;
    const devSpacing = 38;
    const devLeadLeft = `calc(15% + ${(devCount - 1) * devSpacing / 2}px - ${(devCount - 1) * devSpacing / 2}px)`;
    
    user.style.cssText += '; top:60px; left:105px;';
    pm.style.cssText += '; top:60px; right:105px;';
    if (qa) qa.style.cssText += '; bottom:60px; right:125px;';

    const userEmoji = latestFeedback.avatar || '🤬';

    // ── FASE 1: Usuário vai ao TI e registra a melhoria ────
    await wait(400);
    await moveAvatar('avatar-user', { left: '200px' });
    showBubble('bubble-user', `${userEmoji} "${latestFeedback.complaint.substring(0, 40)}..."`, 3000);
    await wait(3200);

    if (latestFeedback.status !== 'accepted') {
        // PM aparece e rejeita
        await moveAvatar('avatar-pm', { right: 'calc(100% - 260px)', top: '60px' });
        showBubble('bubble-pm', "📋 \"Duplicado ou fora do escopo, vou rejeitar!\"", 2800);
        await wait(2800);
        await moveAvatar('avatar-pm', { right: '105px' });
        await moveAvatar('avatar-user', { left: '105px' });
        showBubble('bubble-user', `${userEmoji} \"Entendido... 😤\"`, 2000);
        await wait(2200);
        isOfficeAnimating = false;
        return;
    }

    // ── FASE 2: PM vai ao TI, recebe e cria card no backlog ─
    await moveAvatar('avatar-pm', { right: 'calc(100% - 250px)', top: '60px' });
    showBubble('bubble-pm', "📋 \"Recebi! Vou criar um card no backlog agora.\"", 2500);
    await wait(2700);
    await moveAvatar('avatar-pm', { right: '105px' });
    showBubble('bubble-pm', "📋 \"Card criado! Mandando pro Dev...\"", 2000);
    await wait(2200);

    // ── FASE 3: PM notifica Dev, Dev começa a codar ────────
    const dev0 = document.getElementById('avatar-dev-0');
    if (dev0) {
        showBubble('bubble-dev', `👨‍💻 "Recebi do PM! Iniciando sprint..."`, 2800);
        await wait(3000);
    }

    // ── FASE 4: Loop QA ↔ Dev (simula até 2 rejeições) ────
    const qaAttempts = Math.random() < 0.45 ? 2 : (Math.random() < 0.5 ? 1 : 0);
    const qaConsole = document.getElementById('qa-console-text');

    for (let attempt = 0; attempt < qaAttempts; attempt++) {
        // Dev envia para QA
        if (dev0) { dev0.style.bottom = '60px'; dev0.style.right = '130px'; dev0.style.left = 'auto'; }
        showBubble('bubble-dev', `👨‍💻 "Implementei! Mandando pra QA... (v${attempt + 1})"`, 2500);
        if (qaConsole) qaConsole.innerHTML = `> Recebendo build v${attempt + 1} do Dev...\n> Rodando pytest...`;
        await wait(2700);

        // QA encontra falha e devolve
        if (qa) qa.style.cssText += '; bottom:120px; right:300px;';
        showBubble('bubble-qa', `🧪 "v${attempt + 1}: ${attempt === 0 ? 'Falhou no pytest!' : 'Ainda há edge cases!'} Voltando ao Dev."`, 3000);
        if (qaConsole) qaConsole.innerHTML = `> ❌ Falha detectada na v${attempt + 1}!\n> Enviando relatório de bugs ao Dev...`;
        await wait(3200);

        // QA volta para estação
        if (qa) qa.style.cssText += '; bottom:60px; right:125px;';

        // Dev recebe feedback e corrige
        if (dev0) { dev0.style.right = 'auto'; dev0.style.bottom = '50px'; dev0.style.left = 'calc(15%)'; }
        showBubble('bubble-dev', `👨‍💻 "Falhou! Corrigindo os bugs...  🔧"`, 2800);
        await wait(3000);
    }

    // ── FASE 5: QA aprova e pede validação do cliente ──────
    if (dev0) { dev0.style.bottom = '60px'; dev0.style.right = '130px'; dev0.style.left = 'auto'; }
    showBubble('bubble-dev', "👨‍💻 \"Build final pronto, mandando pra QA!\"", 2500);
    if (qaConsole) qaConsole.innerHTML = '> Recebendo build final...\n> Rodando suite completa de testes...';
    await wait(2700);

    if (qa) qa.style.cssText += '; bottom:120px; right:300px;';
    showBubble('bubble-qa', "🧪 \"✅ 100%! Todos os testes passaram!\"", 2800);
    if (qaConsole) qaConsole.innerHTML = '> ✅ Suite completa aprovada!\n> Solicitando validação do cliente...';
    await wait(3000);

    // QA vai até o TI pedir validação do cliente
    if (qa) qa.style.cssText += '; bottom:200px; right:calc(100% - 250px);';
    showBubble('bubble-qa', "🧪 \"Tudo ok! Pode validar a melhoria?\"", 2800);
    await wait(3000);

    // ── FASE 6: Usuário valida e aprova ────────────────────
    const userApproves = Math.random() < 0.8; // 80% de chance de aprovar
    if (userApproves) {
        showBubble('bubble-user', `${userEmoji} \"Perfeito! Exatamente o que eu queria! ✅\"`, 3000);
        if (qaConsole) qaConsole.innerHTML = '> 🎉 Cliente aprovou!\n> Commit direto na main. Entrega concluída!';
        await wait(3200);
        if (qa) qa.style.cssText += '; bottom:60px; right:125px;';
        if (dev0) { dev0.style.right = 'auto'; dev0.style.bottom = '50px'; dev0.style.left = 'calc(15%)'; }
        showBubble('bubble-dev', "👨‍💻 \"🎉 Deploy feito! Próxima tarefa!\"", 2500);
    } else {
        showBubble('bubble-user', `${userEmoji} \"Hmm, não era bem isso... 🤔 Volta pro backlog!\"`, 3000);
        if (qaConsole) qaConsole.innerHTML = '> ❌ Cliente rejeitou!\n> Abrindo novo card no backlog para revisão...';
        await wait(3200);
        if (qa) qa.style.cssText += '; bottom:60px; right:125px;';
        showBubble('bubble-pm', "📋 \"Entendido! Vou recriar o card com mais detalhes.\"", 2800);
        if (qaConsole) qaConsole.innerHTML = '> 🔄 Card devolvido ao backlog.\n> Aguardando próximo sprint...';
    }

    // Reset all positions
    await wait(2500);
    user.style.left = '105px';
    pm.style.right = '105px';
    if (qa) qa.style.cssText += '; bottom:60px; right:125px;';
    if (dev0) { dev0.style.right = 'auto'; dev0.style.bottom = '50px'; dev0.style.left = 'calc(15%)'; }
    isOfficeAnimating = false;
}
