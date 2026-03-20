import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import './App.css';

function BrokerDashboard({ token }) {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        fetch(`/api/broker/status?token=${token}`)
            .then(r => r.json())
            .then(d => { setData(d); setLoading(false); });
    }, [token]);

    if (loading) return <div className="p-8 text-center">🎓 Carregando Fila do Broker...</div>;

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">
            <header className="flex justify-between items-center bg-gray-900/40 p-6 rounded-2xl border border-white/5">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent italic">🎓 Knowledge Broker</h1>
                    <p className="text-gray-400">Curadoria e Certificação Autônoma de Agentes</p>
                </div>
                <div className="flex gap-4">
                  <div className="bg-gray-800/80 p-4 rounded-xl border border-white/5 text-center px-8">
                      <div className="text-xs text-blue-400 uppercase font-bold tracking-widest">Aprovados</div>
                      <div className="text-2xl font-mono text-white mt-1">{data.summary.certified}</div>
                  </div>
                  <div className="bg-gray-800/80 p-4 rounded-xl border border-white/5 text-center px-8">
                      <div className="text-xs text-red-400 uppercase font-bold tracking-widest">Reprovados</div>
                      <div className="text-2xl font-mono text-white mt-1">{data.summary.failed}</div>
                  </div>
                  <div className="bg-gray-800/80 p-4 rounded-xl border border-white/5 text-center px-8">
                      <div className="text-xs text-yellow-500 uppercase font-bold tracking-widest">Fila</div>
                      <div className="text-2xl font-mono text-white mt-1">{data.summary.pending}</div>
                  </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 bg-gray-900/40 rounded-2xl border border-white/5 overflow-hidden">
                    <div className="p-4 bg-white/5 font-bold flex justify-between">
                        <span>Status de Certificação</span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-white/5 text-gray-500 text-xs uppercase">
                                <tr>
                                    <th className="p-4">Agente</th>
                                    <th className="p-4">Status</th>
                                    <th className="p-4">Data</th>
                                    <th className="p-4">Tries</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5 text-sm">
                                {data.agents.map(a => (
                                    <tr key={a.agent_name} className="hover:bg-white/5 transition-colors">
                                        <td className="p-4 flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center text-xs">
                                                {a.agent_name[0]}
                                            </div>
                                            <span className="font-medium">{a.agent_name}</span>
                                        </td>
                                        <td className="p-4">
                                            {a.certified ? 
                                                <span className="text-emerald-400 flex items-center gap-1">✅ Certificado</span> : 
                                                (a.certified === false ? <span className="text-red-400 flex items-center gap-1">❌ Reprovado</span> : <span className="text-gray-500">⏳ Pendente</span>)}
                                        </td>
                                        <td className="p-4 text-gray-500">{a.certified_at?.split('T')[0] || '-'}</td>
                                        <td className="p-4 text-gray-500 font-mono">{a.certification_attempts || 0}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-gray-900/40 p-6 rounded-2xl border border-blue-500/20">
                        <h3 className="text-blue-400 font-bold mb-4 flex items-center gap-2">🔄 Último Ciclo Autônomo</h3>
                        {data.last_cycle ? (
                            <div className="space-y-4">
                                <div className="text-sm text-gray-300">
                                    <div className="flex justify-between border-b border-white/5 py-2">
                                        <span>Data:</span> <span>{data.last_cycle.timestamp.split('T')[0]}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 py-2">
                                        <span>Tokens Usados:</span> <span className="text-yellow-500 font-mono">{data.last_cycle.tokens_used_estimate}</span>
                                    </div>
                                </div>
                                <div className="p-3 bg-black/40 rounded-lg text-xs font-mono text-emerald-400 border border-emerald-500/20">
                                    ✨ {data.last_cycle.certified.length} agentes certificados
                                </div>
                                <div className="p-3 bg-black/40 rounded-lg text-xs font-mono text-red-400 border border-red-500/20">
                                    🛠️ {data.last_cycle.failed.length} melhorias geradas
                                </div>
                            </div>
                        ) : <p className="text-gray-500 text-sm italic">Nenhum ciclo registrado ainda.</p>}
                    </div>
                </div>
            </div>
        </div>
    );
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!sessionStorage.getItem('flose_token'));
  const [token, setToken] = useState(sessionStorage.getItem('flose_token') || '');
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [key, setKey] = useState('');
  const [error, setError] = useState(false);
  const [stats, setStats] = useState({
    tokens: '0k',
    cost: '$0.00',
    tasks: 0,
    agents: 0
  });
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [activity, setActivity] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [agentList, setAgentList] = useState([]);
  const [executingAgent, setExecutingAgent] = useState('');
  const [executionPreview, setExecutionPreview] = useState(null); // TASK-06
  const [visionAnalysis, setVisionAnalysis] = useState(null);
  const [viewingAgent, setViewingAgent] = useState(null);
  const [pipeline, setPipeline] = useState([]);
  const [pipelineResults, setPipelineResults] = useState([]);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [marketTemplates, setMarketTemplates] = useState([]);
  const [isFixing, setIsFixing] = useState(false);
  const [viewingDelivery, setViewingDelivery] = useState(null);
  
  // QA Report State
  const [qaReport, setQaReport] = useState(null);
  const [qaLoading, setQaLoading] = useState(false);
  const [doraData, setDoraData] = useState(null);
  const [expandedAgent, setExpandedAgent] = useState(null);
  const [enrichingAgent, setEnrichingAgent] = useState(null);

  // Buscar dados reais da API
  const fetchData = async () => {
    if (!token) return;
    try {
      const options = {
        headers: { 'Authorization': `Bearer ${token}` }
      };
      
      const [statsRes, graphRes, tasksRes, activityRes, agentsRes] = await Promise.all([
        fetch(`/api/stats`, options),
        fetch(`/api/graph`, options),
        fetch(`/api/tasks`, options),
        fetch(`/api/activity`, options),
        fetch(`/api/agents`, options)
      ]);
      
      const statsData = await statsRes.json();
      const graphD = await graphRes.json();
      const tasksD = await tasksRes.json();
      const activityD = await activityRes.json();
      
      if (!statsData.error) setStats(statsData);
      if (!graphD.error) setGraphData(graphD);
      if (!tasksD.error) setTasks(tasksD);
      if (!activityD.error) setActivity(activityD);

      const agentsD = await agentsRes.json();
      if (!agentsD.error) setAgentList(agentsD);

      const marketRes = await fetch(`/api/marketplace`, options);
      const marketD = await marketRes.json();
      if (!marketD.error) setMarketTemplates(marketD);
    } catch (err) {
      console.error("Fetch error", err);
    }
  };

  const handleApprove = async (taskId) => {
    await fetch(`/api/tasks/approve?task_id=${taskId}`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    fetchData();
  };

  const handleExecute = async (taskId) => {
    if (!executingAgent) return alert("Selecione um agente!");
    const res = await fetch(`/api/tasks/execute?task_id=${taskId}&agent_name=${executingAgent}`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    alert(data.status === 'success' ? "Tarefa executada com sucesso!" : "Erro: " + data.error);
    fetchData();
  };

  const handleViewDelivery = async (resultId) => {
    try {
      const res = await fetch(`/api/tasks/delivery/${resultId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      // Mesmo se houver erro, setamos o objeto para o modal abrir com a mensagem de erro formatada
      setViewingDelivery(data);
    } catch (err) {
      setViewingDelivery({ error: "Conectividade falhou: " + err.message });
    }
  };

  const handleAgentQuery = async (query) => {
    const res = await fetch(`/api/agents/chat`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    alert("🤖 Response: " + data.response);
    fetchData();
  };

  const handleExport = async (name) => {
    const res = await fetch(`/api/marketplace/export/${name}`, { 
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    alert(data.status === 'success' ? "Agente exportado como template!" : "Erro ao exportar");
    fetchData();
  };

  const handleImport = async (templateName) => {
    const res = await fetch(`/api/marketplace/import`, { 
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ template_name: templateName })
    });
    const data = await res.json();
    alert(data.status === 'success' ? "Template importado com sucesso!" : "Erro ao importar");
    fetchData();
  };

  const handleQAAutoFix = async () => {
    setIsFixing(true);
    try {
      const resp = await fetch(`/api/qa/auto-fix`, { 
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await resp.json();
      alert(`Correction Result: ${data.result}`);
      fetchData();
    } catch (err) {
      console.error("Auto-fix error", err);
    } finally {
      setIsFixing(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 30000); 
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  const handleUpdateStatus = async (taskId, newStatus, newPriority = null) => {
    try {
      let url = `/api/tasks/update-status?task_id=${taskId}`;
      if (newStatus) url += `&new_status=${newStatus}`;
      if (newPriority) url += `&new_priority=${newPriority}`;
      
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.status === 'success') fetchData();
    } catch (err) {
      console.error("Update status error", err);
    }
  };

  const handleAuditFinOps = async (taskId) => {
    try {
      console.log("Starting audit for", taskId);
      const res = await fetch(`/api/tasks/audit-finops?task_id=${taskId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert("Auditoria concluída com sucesso!");
        fetchData();
      } else {
        alert("Erro na auditoria: " + (data.error || "Erro desconhecido"));
      }
    } catch (err) {
      console.error("Audit error", err);
      alert("Falha de rede na auditoria.");
    }
  };

  const fetchQAReport = async () => {
    if (!token) return;
    setQaLoading(true);
    try {
      const res = await fetch('/api/qa/report', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!data.error) setQaReport(data);
    } catch (err) {
      console.error("QA Report fetch error", err);
    } finally {
      setQaLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated, activeTab]);

  useEffect(() => {
    let interval;
    if (isAuthenticated && (activeTab === 'Dashboard' || activeTab === 'Task Manager')) {
      interval = setInterval(fetchData, 30000); 
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isAuthenticated, activeTab]);

  useEffect(() => {
    if (activeTab === 'Quality Inspector') {
      fetchQAReport();
    }
  }, [activeTab]);

  const fetchDoraData = async () => {
    if (!token) return;
    try {
      const res = await fetch('/api/dora/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!data.error) setDoraData(data);
    } catch (err) {
      console.error("DORA fetch error", err);
    }
  };

  useEffect(() => {
    if (activeTab === 'DORA Metrics') {
      fetchDoraData();
    }
  }, [activeTab, isAuthenticated]);

  const handleEnrichAgent = async (agentName) => {
    setEnrichingAgent(agentName);
    try {
      const resp = await fetch(`/api/qa/enrich-agent?agent_name=${encodeURIComponent(agentName)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await resp.json();
      if (data.status === 'success') {
        alert(data.message);
        fetchQAReport();
        fetchData(); 
      } else {
        alert("Erro: " + (data.error || "Falha desconhecida"));
      }
    } catch (err) {
      console.error("Enrich error", err);
      alert("Erro de conexão ou no servidor. Verifique o console.");
    } finally {
      setEnrichingAgent(null);
    }
  };

  // Hook de Física Avançado v4
  // NapkinVisual: exibe diagrama via proxy autenticado (Napkin requer Bearer token)
  const NapkinVisual = ({ visualUrl }) => {
    if (!visualUrl) return null;
    const proxied = `/api/marketplace/visual-proxy?url=${encodeURIComponent(visualUrl)}`;
    return (
      <div style={{ marginTop: '12px', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(52,211,153,0.3)', background: '#111' }}>
        <img 
          src={proxied} 
          style={{ width: '100%', display: 'block', maxHeight: '200px', objectFit: 'contain' }}
          alt="Diagram"
          onError={(e) => { e.target.style.display = 'none'; }}
          onLoad={(e) => {
            // Se for SVG via Proxy, precisamos injetar o token no src se não estiver pegando do global (mas img src não manda header auth customizado fácil)
            // Para imagens, mantemos query param por enquanto OU usamos fetch + blob URL
          }}
          // Melhorei a visão para ser via fetch e blob para suportar header auth
        />
      </div>
    );
  };

  const SlantButton = ({ children, active, onClick, color = '#00f2ff' }) => (
    <button
      onClick={onClick}
      style={{
        padding: "8px 22px",
        fontSize: "11px",
        fontWeight: "800",
        cursor: "pointer",
        border: "none",
        background: active ? color : "rgba(255,255,255,0.03)",
        color: active ? "#000" : "rgba(255,255,255,0.6)",
        transform: "skew(-15deg)",
        transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        boxShadow: active ? `0 0 20px ${color}66` : "none",
        marginRight: "10px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minWidth: "100px",
        textTransform: "uppercase",
        letterSpacing: "1px",
        border: active ? "none" : "1px solid rgba(255,255,255,0.1)"
      }}
    >
      <span style={{ transform: "skew(15deg)" }}>{children}</span>
    </button>
  );


  // --- NANO FORCE ENGINE (Custom Physics from SSIS Reference) ---
  const useForceMap = (nodes, edges, w, h) => {
    const pos = useRef({});
    const vel = useRef({});
    const iter = useRef(0);
    const raf = useRef(null);
    const [, tick] = useState(0);

    useEffect(() => {
      if (!w || !h || !nodes.length) return;
      const cx = w / 2, cy = h / 2;
      const types = ["core", "pilar", "concept"];
      const clusterR = Math.min(w, h) * 0.35;

      nodes.forEach(n => {
        if (pos.current[n.id]) return;
        const ti = types.indexOf(n.type);
        const angle = (2 * Math.PI * ti) / types.length;
        pos.current[n.id] = { x: cx + clusterR * Math.cos(angle) + (Math.random()-.5)*100, y: cy + clusterR * Math.sin(angle) + (Math.random()-.5)*100 };
        vel.current[n.id] = { x:0, y:0 };
      });
      iter.current = 0;

      const clusterCenters = {};
      types.forEach((t, ti) => {
        const angle = (2 * Math.PI * ti) / types.length;
        clusterCenters[t] = { x: cx + clusterR * Math.cos(angle), y: cy + clusterR * Math.sin(angle) };
      });

      const step = () => {
        iter.current++;
        const a = Math.max(0.005, 0.7 * Math.exp(-iter.current * 0.015));
        const p = pos.current, v = vel.current;
        const ids = nodes.map(n => n.id);

        // Repulsion
        for (let i = 0; i < ids.length; i++)
          for (let j = i+1; j < ids.length; j++) {
            const A = ids[i], B = ids[j];
            const dx = p[B].x-p[A].x, dy = p[B].y-p[A].y;
            const d = Math.sqrt(dx*dx+dy*dy)||1;
            const f = (3500/(d*d))*a;
            v[A].x -= dx/d*f; v[A].y -= dy/d*f;
            v[B].x += dx/d*f; v[B].y += dy/d*f;
          }

        // Attraction (Links)
        edges.forEach(e => {
          const s = typeof e.source === 'object' ? e.source.id : e.source;
          const t = typeof e.target === 'object' ? e.target.id : e.target;
          if (!p[s]||!p[t]) return;
          const dx = p[t].x-p[s].x, dy = p[t].y-p[s].y;
          const d = Math.sqrt(dx*dx+dy*dy)||1;
          const ideal = 140;
          const f = ((d-ideal)/d)*0.08*a;
          v[s].x+=dx*f; v[s].y+=dy*f;
          v[t].x-=dx*f; v[t].y-=dy*f;
        });

        // Clustering
        nodes.forEach(n => {
          const cc = clusterCenters[n.type];
          if (!cc) return;
          v[n.id].x += (cc.x-p[n.id].x)*0.03*a;
          v[n.id].y += (cc.y-p[n.id].y)*0.03*a;
        });

        // Integration
        ids.forEach(id => {
          v[id].x*=0.75; v[id].y*=0.75;
          p[id].x = Math.max(65, Math.min(w-65, p[id].x+v[id].x));
          p[id].y = Math.max(65, Math.min(h-65, p[id].y+v[id].y));
        });

        tick(t=>t+1);
        if (a > 0.007) raf.current = requestAnimationFrame(step);
      };

      if (raf.current) cancelAnimationFrame(raf.current);
      raf.current = requestAnimationFrame(step);
      return () => { if (raf.current) cancelAnimationFrame(raf.current); };
    }, [nodes.length, edges.length, w, h]);

    return pos.current;
  };

  const CognitiveMap = ({ data }) => {
    const rawNodes = data?.nodes || [];
    const rawLinks = data?.links || [];
    const containerRef = useRef(null);
    const [dims, setDims] = useState({ w:900, h:640 });
    const [selected, setSelected] = useState(null);
    const [hovered, setHovered] = useState(null);
    const [filterType, setFilterType] = useState("all");
    const [searchTerm, setSearchTerm] = useState('');
    
    const dragOff = useRef({ x:0, y:0 });
    const [dragging, setDragging] = useState(null);
    const posOverride = useRef({});
    const [, forceUpdate] = useState(0);

    useEffect(() => {
      const obs = new ResizeObserver(e => {
        const { width, height } = e[0].contentRect;
        setDims({ w: Math.max(600, width), h: Math.max(460, height) });
      });
      if (containerRef.current) obs.observe(containerRef.current);
      return () => obs.disconnect();
    }, []);

    // 1. DATA MAPPING
    const visNodes = React.useMemo(() => {
      let result = filterType === "all" ? rawNodes : rawNodes.filter(n => n.type === filterType);
      if (searchTerm) result = result.filter(n => n.id.toLowerCase().includes(searchTerm.toLowerCase()));
      return result;
    }, [rawNodes, filterType, searchTerm]);

    const visIds = new Set(visNodes.map(n => n.id));
    const visLinks = rawLinks.filter(l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return visIds.has(sId) && visIds.has(tId);
    });

    const simPos = useForceMap(visNodes, visLinks, dims.w, dims.h);
    const getP = id => posOverride.current[id] || simPos[id] || { x:dims.w/2, y:dims.h/2 };

    const activeIds = React.useMemo(() => {
      const active = selected || hovered;
      if (!active) return new Set();
      const connected = visLinks.filter(l => {
        const s = typeof l.source === 'object' ? l.source.id : l.source;
        const t = typeof l.target === 'object' ? l.target.id : l.target;
        return s === active.id || t === active.id;
      });
      const ids = new Set(connected.flatMap(l => {
        const s = typeof l.source === 'object' ? l.source.id : l.source;
        const t = typeof l.target === 'object' ? l.target.id : l.target;
        return [s, t];
      }));
      ids.add(active.id);
      return ids;
    }, [selected, hovered, visLinks]);

    const onMD = (e, n) => {
      e.stopPropagation();
      const p = getP(n.id), svg = e.currentTarget.closest("svg"), r = svg.getBoundingClientRect();
      dragOff.current = { x: e.clientX-r.left-p.x, y: e.clientY-r.top-p.y };
      setDragging(n.id); setSelected(n);
    };

    useEffect(() => {
      if (!dragging) return;
      const mv = e => {
        const svg = containerRef.current?.querySelector("svg");
        if (!svg) return;
        const r = svg.getBoundingClientRect();
        posOverride.current[dragging] = {
          x: Math.max(65, Math.min(dims.w-65, e.clientX-r.left-dragOff.current.x)),
          y: Math.max(65, Math.min(dims.h-65, e.clientY-r.top-dragOff.current.y)),
        };
        forceUpdate(v=>v+1);
      };
      const up = () => setDragging(null);
      window.addEventListener("mousemove", mv); window.addEventListener("mouseup", up);
      return () => { window.removeEventListener("mousemove", mv); window.removeEventListener("mouseup", up); };
    }, [dragging, dims]);

    const colors = { core: "#3b82f6", pilar: "#f59e0b", concept: "#22c55e", border: "#0d1117", muted: "#334155" };

    return (
      <div style={{ 
        width:"100%", height:"100%", background:"#050810", display:"flex", 
        fontFamily:"'JetBrains Mono','Fira Code',monospace", overflow:"hidden", border:"1px solid #0d1117", borderRadius:12 
      }}>
        
        {/* Main Interface */}
        <div ref={containerRef} style={{ flex:1, position:"relative", overflow:"hidden" }} onClick={() => setSelected(null)}>
          <div style={{ position:"absolute", top:15, left:20, zIndex:10 }}>
            <div style={{ color:"#60a5fa", fontSize:10, fontWeight:700, letterSpacing:2 }}>COGNITIVE_MAP_v5.2 · TECHNICAL_CORE</div>
            <div style={{ color:colors.muted, fontSize:8, marginTop:4 }}>{visNodes.length} nodes active · Cluster scale 0.35</div>
          </div>

          <div style={{ position:"absolute", top:15, right:20, zIndex:10, display:"flex", gap:10 }}>
            <input 
              type="text" placeholder="SEARCH_ID..." value={searchTerm} onChange={e=>setSearchTerm(e.target.value)}
              style={{ background:"transparent", border:"1px solid #0d1117", borderRadius:4, padding:"4px 10px", color:"#fff", fontSize:9, outline:"none", width:120 }}
            />
            <div style={{ display:"flex", gap:4 }}>
              {["all", "core", "pilar", "concept"].map(t => (
                <button key={t} onClick={() => setFilterType(t)} style={{
                  padding:"3px 8px", fontSize:8, borderRadius:3, cursor:"pointer", background:filterType===t?"#1e293b":"transparent",
                  border:`1px solid ${filterType===t?"#3b82f6":"#0d1117"}`, color:filterType===t?"#60a5fa":colors.muted, fontFamily:"inherit"
                }}>{t.toUpperCase()}</button>
              ))}
            </div>
          </div>

          <svg width={dims.w} height={dims.h} style={{ display:"block" }}>
            <defs>
              <filter id="nodeGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
            </defs>

            {/* Links */}
            {visLinks.map((l, i) => {
              const sId = typeof l.source === 'object' ? l.source.id : l.source;
              const tId = typeof l.target === 'object' ? l.target.id : l.target;
              const sp = getP(sId), tp = getP(tId);
              if (!sp || !tp) return null;
              const isAct = (selected?.id === sId || selected?.id === tId) || (hovered?.id === sId || hovered?.id === tId);
              return (
                <line key={i} x1={sp.x} y1={sp.y} x2={tp.x} y2={tp.y} 
                  stroke={isAct ? "#60a5fa" : "#0f172a"} 
                  strokeWidth={isAct ? 1.5 : 0.8}
                  strokeOpacity={isAct ? 1 : 0.4}
                />
              );
            })}

            {/* Nodes */}
            {visNodes.map(n => {
              const p = getP(n.id); if (!p) return null;
              const isSel = selected?.id === n.id, isHov = hovered?.id === n.id;
              const isDim = (selected || hovered) && !activeIds.has(n.id);
              const col = colors[n.type] || "#fff";
              const r = n.type === 'core' ? 18 : (n.type === 'pilar' ? 12 : 8);

              return (
                <g key={n.id} transform={`translate(${p.x},${p.y})`} style={{ cursor:"grab" }}
                  onMouseDown={e => onMD(e, n)} onMouseEnter={() => setHovered(n)} onMouseLeave={() => setHovered(null)}
                  onClick={e => { e.stopPropagation(); setSelected(n); }}>
                  
                  {n.type === 'core' && <circle r={r+6} fill="none" stroke={col} strokeWidth={1} strokeDasharray="3 3" strokeOpacity={isDim?.1:.4}/>}
                  {(isSel || isHov) && <circle r={r+4} fill={col} fillOpacity={0.15} style={{ filter:"url(#nodeGlow)" }}/>}
                  
                  <circle r={r} fill={isDim ? "#0d1117" : col} fillOpacity={isDim ? 0.1 : 0.9} stroke={isSel ? "#fff" : col} strokeWidth={isSel ? 2 : 1}/>
                  
                  <text y={r+14} textAnchor="middle" fontSize={8} fill={isDim ? "#0d1117" : "#94a3b8"} fontWeight={isSel ? 700 : 400} style={{ pointerEvents:"none", userSelect:"none" }}>
                    {n.id.length > 20 ? n.id.slice(0, 18) + '…' : n.id.toUpperCase()}
                  </text>
                  {n.type === 'core' && !isDim && (
                    <text dominantBaseline="middle" textAnchor="middle" fontSize={9} fill="#fff" fontWeight="900" style={{ pointerEvents:"none" }}>★</text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* SOBER LEGEND */}
          <div style={{ position:"absolute", bottom:20, left:20, background:"rgba(5,8,16,.85)", border:"1px solid #0d1117", borderRadius:6, padding:"10px 14px", pointerEvents:"none" }}>
            <div style={{ color:colors.muted, fontSize:7, letterSpacing:2, marginBottom:6 }}>SYSTEM_INDEX</div>
            {["core", "pilar", "concept"].map(t => (
              <div key={t} style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
                <div style={{ width:6, height:6, borderRadius:"50%", background:colors[t] }}/>
                <span style={{ color:"#64748b", fontSize:8 }}>{t.toUpperCase()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Technical Side Panel */}
        <div style={{ 
          width:selected ? 300 : 0, flexShrink:0, background:"#05080e", borderLeft:"1px solid #0d1117", 
          overflow:"hidden", transition:"width .25s cubic-bezier(0.19, 1, 0.22, 1)", display:"flex", flexDirection:"column" 
        }}>
          {selected && (
            <div style={{ padding:25, flex:1, overflowY:"auto" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:15 }}>
                <span style={{ color:colors[selected.type], fontSize:9, fontWeight:700, letterSpacing:2 }}>NODE_ID: {selected.id.slice(0,8)}</span>
                <button onClick={() => setSelected(null)} style={{ background:"none", border:"none", color:"#1e293b", cursor:"pointer", fontSize:14 }}>✕</button>
              </div>

              <div style={{ color:"#e2e8f0", fontSize:16, fontWeight:900, lineHeight:1.2, marginBottom:15 }}>{selected.id.toUpperCase()}</div>

              <div style={{ display:"flex", gap:10, marginBottom:25 }}>
                <div style={{ flex:1, background:"#0a0f1a", border:"1px solid #0d1117", borderRadius:6, padding:10, textAlign:"center" }}>
                   <div style={{ color:colors[selected.type], fontSize:18, fontWeight:900 }}>{visLinks.filter(l => (typeof l.source === 'object' ? l.source.id : l.source) === selected.id || (typeof l.target === 'object' ? l.target.id : l.target) === selected.id).length}</div>
                   <div style={{ color:colors.muted, fontSize:7, marginTop:2 }}>CONNECTIONS</div>
                </div>
                <div style={{ flex:1, background:"#0a0f1a", border:"1px solid #0d1117", borderRadius:6, padding:10, textAlign:"center" }}>
                   <div style={{ color:"#fff", fontSize:18, fontWeight:900 }}>100%</div>
                   <div style={{ color:colors.muted, fontSize:7, marginTop:2 }}>RELIABILITY</div>
                </div>
              </div>

              <div style={{ color:colors.muted, fontSize:7, letterSpacing:2, marginBottom:10, borderBottom:"1px solid #0d1117", paddingBottom:8 }}>SEMANTIC_LAYER</div>
              <p style={{ color:"#94a3b8", fontSize:10, lineHeight:1.6, marginBottom:30 }}>
                {selected.type === 'core' ? 'Primary intelligence nexus. Orchestrates and validates all subordinate technical pilots and atomic data nodes within the Flose framework.' : 
                 selected.type === 'pilar' ? 'Technical vertical pillar. Aggregates specialized concept clusters to provide higher-order cognitive processing.' : 
                 'Atomic intelligence concept. Fundamental persistent unit of knowledge extracted and verified during autonomous agent operations.'}
              </p>

              <div style={{ color:colors.muted, fontSize:7, letterSpacing:2, marginBottom:12 }}>CONNECTED_DEPENDENCIES</div>
              <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                {visLinks.filter(l => (typeof l.source === 'object' ? l.source.id : l.source) === selected.id || (typeof l.target === 'object' ? l.target.id : l.target) === selected.id).map((l, i) => {
                  const other = (typeof l.source === 'object' ? l.source.id : l.source) === selected.id ? (typeof l.target === 'object' ? l.target.id : l.target) : (typeof l.source === 'object' ? l.source.id : l.source);
                  const node = rawNodes.find(n => n.id === other);
                  return (
                    <div key={i} onClick={() => setSelected(node)} style={{ 
                      background:"#0a0f1a", border:"1px solid #0d1117", borderRadius:6, padding:10, cursor:"pointer", transition:"border 0.2s" 
                    }} onMouseEnter={e => e.currentTarget.style.borderColor = colors[node?.type] || "#fff"}>
                      <div style={{ color:"#fff", fontSize:9, fontWeight:700 }}>{other.toUpperCase()}</div>
                      <div style={{ color:colors[node?.type] || colors.muted, fontSize:7, marginTop:2 }}>RELATION: {l.relation?.toUpperCase() || "CONNECTED"}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };


  const renderContent = () => {
    if (activeTab === 'Dashboard') {
      return (
        <>
          <section className="kpi-grid">
            <div className="glass-card">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '10px' }}>Tokens Used Today</p>
              <h3 style={{ fontSize: '2rem' }}>{stats.tokens}</h3>
              <div className="mini-graph" style={{ backgroundColor: 'var(--primary)', height: '4px', width: '60%', marginTop: '10px', borderRadius: '2px' }}></div>
            </div>
            <div className="glass-card">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '10px' }}>Current Daily Spend</p>
              <h3 style={{ fontSize: '2rem' }}>{stats.cost}</h3>
              <p style={{ color: '#00ff80', fontSize: '0.7rem', marginTop: '5px' }}>Real-time GCP Data</p>
            </div>
            <div className="glass-card">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '10px' }}>Active Agents</p>
              <h3 style={{ fontSize: '2rem' }}>{stats.agents}</h3>
            </div>
            <div className="glass-card">
              <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '10px' }}>Pending Tasks</p>
              <h3 style={{ fontSize: '2rem' }}>{stats.tasks}</h3>
              <p style={{ color: stats.tasks > 0 ? '#f59e0b' : '#00ff80', fontSize: '0.7rem', marginTop: '5px' }}>
                {stats.tasks > 0 ? 'Action required' : 'All clear'}
              </p>
            </div>
          </section>

          <section className="content-area" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px' }}>
            <div className="glass-card" style={{ height: '400px', position: 'relative', padding: 0, overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: '20px', left: '25px', zIndex: 5 }}>
                <h4 style={{ marginBottom: '5px', fontSize: '0.9rem' }}>Neural Activity: Cognitive Map</h4>
                <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>LIVE_FEED_002 / REALTIME</p>
              </div>
              <div style={{ height: '100%', width: '100%', background: 'radial-gradient(circle at center, #0a0e1a 0%, #050505 100%)' }}>
                <svg width="100%" height="100%" viewBox="0 0 800 400">
                  {graphData.links && graphData.links.map((link, i) => {
                    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                    const s = graphData.nodes.find(n => n.id === sourceId);
                    const t = graphData.nodes.find(n => n.id === targetId);
                    if (!s || !t) return null;
                    
                    // Layout simplificado para preview (circular)
                    const sIdx = graphData.nodes.indexOf(s);
                    const tIdx = graphData.nodes.indexOf(t);
                    const sx = s.type === 'core' ? 400 : 400 + Math.cos(sIdx) * 120;
                    const sy = s.type === 'core' ? 200 : 200 + Math.sin(sIdx) * 100;
                    const tx = t.type === 'core' ? 400 : 400 + Math.cos(tIdx) * 120;
                    const ty = t.type === 'core' ? 200 : 200 + Math.sin(tIdx) * 100;

                    return <line key={i} x1={sx} y1={sy} x2={tx} y2={ty} stroke="var(--primary)" strokeOpacity="0.15" />;
                  })}
                  {graphData.nodes && graphData.nodes.slice(0, 20).map((node, i) => {
                    const x = node.type === 'core' ? 400 : 400 + Math.cos(i) * 120;
                    const y = node.type === 'core' ? 200 : 200 + Math.sin(i) * 100;
                    return (
                      <g key={node.id} transform={`translate(${x}, ${y})`}>
                        <circle r={node.type === 'core' ? 8 : 4} fill={node.type === 'core' ? 'var(--primary)' : (node.type === 'pilar' ? '#f59e0b' : '#34d399')} filter={node.type === 'core' ? "blur(2px)" : ""} />
                        <text dy="15" textAnchor="middle" fill="white" fontSize="6" style={{ opacity: 0.5 }}>{node.id.substring(0, 10)}</text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
            <div className="glass-card">
              <h4 style={{ marginBottom: '20px' }}>Recent Activity (Telegram)</h4>
              <div className="audit-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {activity.length > 0 ? activity.map((act, i) => (
                  <div key={i} className="audit-item" style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                    <p style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--primary)' }}>@{act.user}</p>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{act.message ? act.message.substring(0, 40) + '...' : '[Image/No Text]'}</p>
                    <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>{new Date(act.timestamp).toLocaleTimeString()}</span>
                  </div>
                )) : (
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Waiting for incoming signals...</p>
                )}
              </div>
            </div>
          </section>
        </>
      );
    }

    if (activeTab === 'Cognitive Map') {
      return <CognitiveMap data={graphData} />;
    }

    if (activeTab === 'Task Manager') {
      const columns = [
        { id: 'Aberto', title: '📋 BACKLOG', color: '#f59e0b' },
        { id: 'Em Progresso', title: '⚡ EM EXECUÇÃO', color: 'var(--primary)' },
        { id: 'Concluído', title: '✅ ENTREGUES', color: '#10b981' }
      ];

      const getTasksByStatus = (status) => {
        // Normalização de status para suportar variações legadas
        const map = {
          'Aberto': ['Aberto', 'OPEN', 'backlog'],
          'Em Progresso': ['Em Progresso', 'IN_PROGRESS', 'doing'],
          'Concluído': ['Concluído', 'COMPLETED', 'done']
        };
        const targets = map[status] || [status];
        return tasks.filter(t => targets.includes(t.status));
      };

      const onDragStart = (e, taskId) => {
        e.dataTransfer.setData('taskId', taskId);
      };

      const onDragOver = (e) => {
        e.preventDefault();
      };

      const onDrop = (e, newStatus) => {
        const taskId = e.dataTransfer.getData('taskId');
        handleUpdateStatus(taskId, newStatus);
      };

      return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '25px', height: 'calc(100vh - 250px)', minHeight: '600px' }}>
          {columns.map(col => (
            <div 
              key={col.id} 
              onDragOver={onDragOver}
              onDrop={(e) => onDrop(e, col.id)}
              style={{ 
                background: 'rgba(255,255,255,0.02)', 
                borderRadius: '20px', 
                border: '1px solid var(--border)', 
                display: 'flex', 
                flexDirection: 'column', 
                overflow: 'hidden' 
              }}
            >
              <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', background: `${col.color}08`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ fontSize: '0.85rem', letterSpacing: '2px', color: col.color, fontWeight: '900' }}>{col.title}</h3>
                <span style={{ fontSize: '0.7rem', background: 'rgba(255,255,255,0.05)', padding: '4px 10px', borderRadius: '20px', color: 'var(--text-muted)' }}>
                  {getTasksByStatus(col.id).length}
                </span>
              </div>
              
              <div style={{ flex: 1, padding: '15px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                {getTasksByStatus(col.id).map(task => (
                  <div 
                    key={task.id} 
                    draggable 
                    onDragStart={(e) => onDragStart(e, task.id)}
                    onClick={() => setSelectedTask(task)}
                    className={`glass-card ${selectedTask?.id === task.id ? 'active' : ''}`}
                    style={{ 
                      padding: '18px', 
                      cursor: 'grab', 
                      border: selectedTask?.id === task.id ? `1px solid ${col.color}` : '1px solid var(--border)',
                      position: 'relative',
                      animation: 'fadeIn 0.4s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ fontSize: '0.65rem', color: col.color, fontWeight: '900' }}>{task.id}</span>
                      <span style={{ fontSize: '0.7rem' }}>{task.budget_approved ? '💎' : '⏳'}</span>
                    </div>
                    
                    <h4 style={{ fontSize: '0.9rem', marginBottom: '10px', lineHeight: '1.4' }}>{task.title}</h4>
                    
                    <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '15px', display: '-webkit-box', WebkitLineClamp: '2', WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {task.objective || 'Objetivo não detalhado...'}
                    </p>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="avatar" style={{ width: '24px', height: '24px', fontSize: '0.5rem', background: 'var(--primary)', color: '#000' }}>
                          {task.responsible?.substring(0,2).toUpperCase() || 'IA'}
                        </div>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{task.responsible || 'IA'}</span>
                      </div>
                      <select 
                        value={task.priority || 'Média'}
                        onClick={(e) => e.stopPropagation()}
                        onChange={(e) => handleUpdateStatus(task.id, null, e.target.value)}
                        style={{ 
                          fontSize: '0.55rem', 
                          background: 'rgba(255,255,255,0.08)', 
                          padding: '3px 8px', 
                          borderRadius: '4px',
                          border: 'none',
                          color: '#fff',
                          cursor: 'pointer',
                          outline: 'none'
                        }}
                      >
                        <option value="Alta">Alta</option>
                        <option value="Média">Média</option>
                        <option value="Baixa">Baixa</option>
                      </select>
                    </div>

                    {/* Mostra governança se selecionado */}
                    {selectedTask?.id === task.id && (
                      <div style={{ marginTop: '15px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', borderLeft: `3px solid ${col.color}`, animation: 'slideDown 0.3s ease' }}>
                        <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', fontWeight: 'bold', marginBottom: '5px' }}>🛡️ GOVERNANÇA FINOPS</p>
                        <p style={{ fontSize: '0.7rem', color: '#fff' }}>{task.governance_finops || 'Aguardando auditoria FinOps...'}</p>
                        
                        {(task.governance_finops === 'Aguardando auditoria FinOps...' || !task.objective || task.objective === 'Geração pendente...') && (
                          <button 
                            className="login-button" 
                            style={{ fontSize: '0.65rem', padding: '6px', background: 'rgba(255,255,255,0.1)', marginTop: '10px' }} 
                            onClick={(e) => { e.stopPropagation(); handleAuditFinOps(task.id); }}
                          >
                            🔍 AUDITAR AGORA
                          </button>
                        )}

                        <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                          {!task.budget_approved && col.id === 'Aberto' && (
                            <button className="login-button" style={{ fontSize: '0.65rem', padding: '6px' }} onClick={() => handleApprove(task.id)}>👍 APROVAR</button>
                          )}
                          {task.status === 'Em Progresso' && task.budget_approved && (
                            <button className="login-button" style={{ fontSize: '0.65rem', padding: '6px', background: 'var(--primary)', color: '#000' }} onClick={() => {
                              setExecutionPreview(task);
                            }}>🚀 EXECUTAR</button>
                          )}
                          {task.status === 'Concluído' && (
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button className="login-button" style={{ fontSize: '0.65rem', padding: '6px', background: '#10b981', flex: 1 }} onClick={() => handleViewDelivery(task.result_id)}>📦 VER</button>
                              <button className="login-button" style={{ fontSize: '0.65rem', padding: '6px', background: 'rgba(255,255,255,0.1)', flex: 1 }} onClick={() => window.open(`/api/tasks/${task.id}/export?token=${token}`)}>💾 MD</button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (activeTab === 'Agent Library') {
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '40px' }}>
          <div className="agent-library-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100%, 1fr))', gap: '20px' }}>
            {agentList.map(agent => (
              <div key={agent.agent_name} className="glass-card agent-card-edit" style={{ display: 'grid', gridTemplateColumns: '80px 1fr 200px', gap: '20px', alignItems: 'center' }}>
                <div className="avatar" style={{ background: 'var(--primary)', color: 'black', width: '60px', height: '60px' }}>
                  {agent.agent_name.substring(0,2).toUpperCase()}
                </div>
                <div>
                  <h3 style={{ color: 'var(--primary)' }}>{agent.agent_name}</h3>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>{agent.purpose}</p>
                  <div style={{ display: 'flex', gap: '15px' }}>
                    <div className="metric-mini">
                      <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>RUNS</span>
                      <p style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{agent.metrics?.executions || 0}</p>
                    </div>
                    <div className="metric-mini">
                      <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>TOKENS</span>
                      <p style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{((agent.metrics?.total_tokens || 0)/1000).toFixed(1)}k</p>
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <button 
                    className="nav-item badge-online" 
                    style={{ padding: '8px 15px', borderRadius: '12px', fontSize: '0.7rem', cursor: 'pointer' }}
                    onClick={() => setViewingAgent(agent)}
                  >
                    🛠️ Manage DNA
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="glass-card chat-side">
            <h3 className="title-grad" style={{ fontSize: '1.4rem' }}>Registry Assistant</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '20px' }}>Ask history or request prompt edits via natural language.</p>
            
            <div className="chat-bubble-area" style={{ height: '300px', background: 'rgba(0,0,0,0.2)', borderRadius: '15px', marginBottom: '15px', padding: '15px', overflowY: 'auto' }}>
              <div className="ai-msg" style={{ fontSize: '0.85rem', color: '#e0e0e0', background: 'var(--glass)', padding: '10px', borderRadius: '12px', marginBottom: '10px' }}>
                "Hi Felipe! I can help you update any agent. Just say: 'Change FinOps purpose to focus on GCP billing' or 'Who is the TaskManager?'"
              </div>
            </div>
            
            <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                placeholder="Type your registry command..." 
                style={{ width: '100%', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '12px', padding: '15px', color: 'white' }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleAgentQuery(e.target.value);
                    e.target.value = ''; // Clear input after sending
                  }
                }}
              />
            </div>
          </div>
        </div>
      );
    }

    if (activeTab === 'Pipeline') {
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '40px' }}>
          <div className="glass-card">
            <h3>🏗️ Pipeline Builder</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '20px' }}>
              Select agents to build a sequential sequence of execution.
            </p>
            
            <div className="pipeline-area" style={{ minHeight: '400px', border: '2px dashed var(--border)', borderRadius: '20px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {pipeline.length === 0 && <p style={{ textAlign: 'center', marginTop: '150px', opacity: 0.3 }}>Pipeline is empty. Add agents from the sidebar.</p>}
              {pipeline.map((step, idx) => (
                <div key={idx} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '15px', border: '1px solid var(--primary)', animation: 'slideUp 0.3s' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div className="avatar" style={{ scale: '0.7', background: 'var(--primary)', color: 'black' }}>{idx + 1}</div>
                    <div>
                      <h4 style={{ color: 'var(--primary)' }}>{step.agent_name}</h4>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{step.task || 'Generic processing...'}</p>
                    </div>
                  </div>
                  <button onClick={() => setPipeline(pipeline.filter((_, i) => i !== idx))} style={{ background: 'none', border: 'none', color: '#ff4d4d', cursor: 'pointer', fontSize: '1.2rem' }}>&times;</button>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '20px', display: 'flex', gap: '15px' }}>
              <button 
                className="login-button" 
                style={{ background: 'var(--primary)', color: 'black', flex: 1 }}
                disabled={pipeline.length === 0 || isRunningPipeline}
                onClick={async () => {
                  setIsRunningPipeline(true);
                  const results = [];
                  for(const step of pipeline) {
                    const res = await fetch(`/api/tasks/execute?task_id=PIPELINE&agent_name=${step.agent_name}`, { 
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${token}` }
                    });
                    const d = await res.json();
                    results.push({ agent: step.agent_name, output: d.result });
                  }
                  setPipelineResults(results);
                  setIsRunningPipeline(false);
                }}
              >
                {isRunningPipeline ? '⏳ EXECUTING SEQUENTIAL OPS...' : '🚀 RUN PIPELINE'}
              </button>
              <button className="refresh-btn" style={{ padding: '0 20px' }} onClick={() => {setPipeline([]); setPipelineResults([]);}}>CLEAR</button>
            </div>
          </div>

          <div className="glass-card">
            <h3 style={{ marginBottom: '20px' }}>Agent Repository</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '400px', overflowY: 'auto', paddingRight: '5px' }}>
              {agentList.map(a => (
                <div key={a.agent_name} className="glass-card" style={{ padding: '15px', cursor: 'pointer', border: '1px solid transparent', transition: 'all 0.2s' }} 
                     onClick={() => {
                       const t = prompt(`Instruction for ${a.agent_name}:`, "Refine the previous output or perform specific analysis.");
                       if (t) setPipeline([...pipeline, { ...a, task: t }]);
                     }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="avatar" style={{ width: '30px', height: '30px', fontSize: '0.6rem' }}>{a.agent_name.substring(0,2)}</div>
                    <div>
                      <p style={{ fontWeight: 'bold', fontSize: '0.85rem' }}>{a.agent_name}</p>
                      <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{a.purpose.substring(0, 40)}...</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {pipelineResults.length > 0 && (
              <div style={{ marginTop: '30px', padding: '20px', background: 'rgba(0,242,255,0.03)', borderRadius: '15px', border: '1px solid var(--border)' }}>
                <h4 style={{ color: 'var(--primary)', marginBottom: '15px', fontSize: '0.9rem' }}>EXECUTION LOG:</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {pipelineResults.map((r, i) => (
                    <details key={i} style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '10px' }}>
                      <summary style={{ cursor: 'pointer', color: 'white', fontSize: '0.8rem', fontWeight: 'bold' }}>Step {i+1}: {r.agent}</summary>
                      <pre style={{ padding: '10px', opacity: 0.8, fontSize: '0.75rem', whiteSpace: 'pre-wrap', marginTop: '10px', borderTop: '1px solid var(--border)' }}>{r.output}</pre>
                    </details>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    if (activeTab === 'Marketplace') {
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '30px' }}>
          <div className="glass-card">
            <h2 className="title-grad" style={{ fontSize: '1.8rem', marginBottom: '10px' }}>Global Agent Marketplace</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '30px' }}>Community-driven templates to scale your infrastructure.</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
              {marketTemplates.length > 0 ? marketTemplates.map(tpl => (
                <div key={tpl.name} className="glass-card agent-card-edit" style={{ border: '1px solid rgba(0,255,128,0.2)', position: 'relative' }}>
                  <div style={{ position: 'absolute', top: '10px', right: '10px', fontSize: '0.6rem', color: 'rgba(0,255,128,0.7)', fontWeight: '900', textTransform: 'uppercase', background: 'rgba(0,255,128,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                    {tpl.category || 'General'}
                  </div>
                  <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '15px' }}>
                    <div className="avatar" style={{ background: '#34d399', color: 'black' }}>{tpl.name[0]}</div>
                    <h4 style={{ color: '#34d399' }}>{tpl.name}</h4>
                  </div>
                  
                  <p style={{ fontSize: '0.8rem', color: '#fff', marginBottom: '10px', fontWeight: '600' }}>{tpl.description || tpl.purpose}</p>
                  
                  {tpl.use_cases && (
                    <div style={{ marginBottom: '15px' }}>
                      <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginBottom: '5px', fontWeight: 'bold' }}>USE CASES:</p>
                      <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                        {tpl.use_cases.map(uc => (
                          <span key={uc} style={{ fontSize: '0.55rem', background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)', padding: '2px 6px', borderRadius: '4px' }}>{uc}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  <NapkinVisual visualUrl={tpl.napkin_visual_url} />

                  <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>By {tpl.author}</span>
                    <button className="nav-item badge-online" style={{ padding: '8px 20px', fontSize: '0.65rem', fontWeight: '900' }} onClick={() => handleImport(tpl.name)}>📥 IMPORT TEMPLATE</button>
                  </div>
                </div>
              )) : (
                <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '100px', opacity: 0.3 }}>
                  <p>No community templates found. Be the first to export!</p>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card">
            <h3 style={{ marginBottom: '20px' }}>My Exportable Agents</h3>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '20px' }}>Turn your local agents into shareable templates.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {agentList.map(a => (
                <div key={a.agent_name} className="glass-card" style={{ padding: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div className="avatar" style={{ width: '32px', height: '32px', fontSize: '0.7rem' }}>{a.agent_name.substring(0,2)}</div>
                    <span style={{ fontSize: '0.85rem' }}>{a.agent_name}</span>
                  </div>
                  <button className="refresh-btn" style={{ padding: '5px 10px', fontSize: '0.6rem' }} onClick={() => handleExport(a.agent_name)}>📤 EXPORT</button>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    }

    if (activeTab === 'FinOps Guardian') {
      return (
        <div className="glass-card">
          <h2 className="title-grad">Billing Dashboard</h2>
          <div style={{ marginTop: '30px' }}>
            <div className="billing-row" style={{ display: 'flex', justifyContent: 'space-between', padding: '15px', borderBottom: '1px solid var(--border)' }}>
              <span>Total Estimated Cost (Cloud Run + Tokens)</span>
              <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{stats.cost}</span>
            </div>
            <div className="billing-row" style={{ display: 'flex', justifyContent: 'space-between', padding: '15px', borderBottom: '1px solid var(--border)' }}>
              <span>Tokens Used (Hoy)</span>
              <span style={{ color: 'var(--primary)' }}>{stats.tokens}</span>
            </div>
            <div className="billing-row" style={{ display: 'flex', justifyContent: 'space-between', padding: '15px', borderBottom: '1px solid var(--border)' }}>
              <span>API Request Volume</span>
              <span style={{ color: 'var(--primary)' }}>{stats.calls || 0} calls</span>
            </div>
          </div>
        </div>
      );
    }

    if (activeTab === 'Quality Inspector') {


      const AccuracyBar = ({ value }) => {
        const color = value >= 80 ? '#00ff80' : value >= 50 ? '#f59e0b' : '#ff4d4d';
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: '140px' }}>
            <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: '4px', transition: 'width 0.6s ease', boxShadow: `0 0 10px ${color}66` }} />
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: '900', color, minWidth: '40px', textAlign: 'right' }}>{value}%</span>
          </div>
        );
      };

      const StatusBadge = ({ status }) => {
        const map = {
          'Concluído': { bg: 'rgba(0,255,128,0.15)', color: '#00ff80', label: '✅ Concluído' },
          'COMPLETED': { bg: 'rgba(0,255,128,0.15)', color: '#00ff80', label: '✅ Completed' },
          'done': { bg: 'rgba(0,255,128,0.15)', color: '#00ff80', label: '✅ Done' },
          'Aberto': { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: '⏳ Aberto' },
          'OPEN': { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: '⏳ Open' },
          'Em Progresso': { bg: 'rgba(0,242,255,0.15)', color: 'var(--primary)', label: '🔄 Em Progresso' },
          'IN_PROGRESS': { bg: 'rgba(0,242,255,0.15)', color: 'var(--primary)', label: '🔄 In Progress' },
        };
        const s = map[status] || { bg: 'rgba(255,255,255,0.08)', color: 'var(--text-muted)', label: status || '❓' };
        return <span style={{ padding: '3px 10px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: '800', background: s.bg, color: s.color }}>{s.label}</span>;
      };

      if (qaLoading || !qaReport) {
        return (
          <div className="glass-card" style={{ textAlign: 'center', padding: '80px' }}>
            <h2 className="title-grad" style={{ marginBottom: '15px' }}>🔍 Quality Inspector</h2>
            <p style={{ color: 'var(--text-muted)' }}>Carregando relatório completo de agentes, tarefas e interações...</p>
            <div style={{ marginTop: '30px', fontSize: '2rem' }}>⏳</div>
          </div>
        );
      }

      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '25px' }}>
          {/* Header com KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px' }}>TOTAL AGENTS</p>
              <p style={{ fontSize: '2.2rem', fontWeight: '900', color: 'var(--primary)' }}>{qaReport.summary.total_agents}</p>
            </div>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px' }}>TOTAL TASKS</p>
              <p style={{ fontSize: '2.2rem', fontWeight: '900', color: '#f59e0b' }}>{qaReport.summary.total_tasks}</p>
            </div>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px' }}>INTERACTIONS</p>
              <p style={{ fontSize: '2.2rem', fontWeight: '900', color: '#34d399' }}>{qaReport.total_interactions}</p>
            </div>
            <div className="glass-card" style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px' }}>AVG ACCURACY</p>
              <p style={{ fontSize: '2.2rem', fontWeight: '900', color: qaReport.summary.avg_accuracy >= 70 ? '#00ff80' : '#ff4d4d' }}>{qaReport.summary.avg_accuracy}%</p>
            </div>
          </div>

          {/* Header da lista + botões */}
          <div className="glass-card" style={{ padding: '20px 30px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 className="title-grad" style={{ fontSize: '1.6rem', marginBottom: '5px' }}>Quality Inspector Report</h2>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Análise completa de cada agente: tarefas, acertividade e interações.</p>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button onClick={fetchQAReport} className="refresh-btn" style={{ padding: '8px 20px' }}>🔄 Atualizar</button>
                <button 
                  onClick={handleQAAutoFix} 
                  disabled={isFixing}
                  className="login-button" 
                  style={{ width: 'auto', padding: '8px 25px', background: 'var(--primary)', fontSize: '0.75rem' }}
                >
                  {isFixing ? '🌀 ANALYZING...' : '⚡ AUTO-FIX'}
                </button>
              </div>
            </div>
          </div>

          {/* Lista de Agentes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {qaReport.agents.map((agent, idx) => {
              const isExpanded = expandedAgent === agent.agent_name;
              return (
                <div key={agent.agent_name} className="glass-card" style={{ padding: 0, overflow: 'hidden', border: isExpanded ? '1px solid var(--primary)' : '1px solid var(--border)', transition: 'all 0.3s' }}>
                  {/* Row principal do agente */}
                  <div 
                    onClick={() => setExpandedAgent(isExpanded ? null : agent.agent_name)}
                    style={{ 
                      display: 'grid', 
                      gridTemplateColumns: '50px 1fr 180px 140px 100px 40px', 
                      alignItems: 'center', 
                      padding: '18px 25px', 
                      cursor: 'pointer',
                      transition: 'background 0.2s',
                      background: isExpanded ? 'rgba(0,242,255,0.03)' : 'transparent'
                    }}
                  >
                    <div className="avatar" style={{ width: '38px', height: '38px', fontSize: '0.7rem', background: agent.accuracy >= 80 ? 'rgba(0,255,128,0.2)' : agent.accuracy >= 50 ? 'rgba(245,158,11,0.2)' : 'rgba(255,77,77,0.2)', color: agent.accuracy >= 80 ? '#00ff80' : agent.accuracy >= 50 ? '#f59e0b' : '#ff4d4d' }}>
                      {agent.agent_name.substring(0,2).toUpperCase()}
                    </div>

                    <div>
                      <h4 style={{ color: '#fff', fontSize: '0.95rem', fontWeight: '700', marginBottom: '3px' }}>{agent.agent_name}</h4>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{agent.purpose.substring(0, 80)}{agent.purpose.length > 80 ? '...' : ''}</p>
                    </div>

                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      <span>📋 {agent.task_summary.total} tasks</span>
                      <span>💬 {agent.total_interactions} interactions</span>
                    </div>

                    <AccuracyBar value={agent.accuracy} />

                    <button 
                      onClick={(e) => { e.stopPropagation(); handleEnrichAgent(agent.agent_name); }}
                      disabled={enrichingAgent === agent.agent_name}
                      style={{
                        background: 'rgba(0,242,255,0.1)',
                        border: '1px solid var(--primary)',
                        color: 'var(--primary)',
                        borderRadius: '6px',
                        padding: '6px 12px',
                        fontSize: '0.65rem',
                        fontWeight: '900',
                        cursor: 'pointer',
                        transition: 'all 0.3s',
                        zIndex: 10
                      }}
                    >
                      {enrichingAgent === agent.agent_name ? '🌀' : '⚡ AJUSTAR'}
                    </button>

                    <div style={{ textAlign: 'right', fontSize: '1.2rem', transition: 'transform 0.3s', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>▾</div>
                  </div>

                  {/* Painel expandido */}
                  {isExpanded && (
                    <div style={{ borderTop: '1px solid var(--border)', padding: '25px', background: 'rgba(0,0,0,0.2)' }}>
                      {/* Config do agente */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '25px' }}>
                        <div style={{ padding: '15px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                          <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px', letterSpacing: '1px' }}>CONFIGURAÇÃO</p>
                          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                            <span style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: '700', background: agent.has_prompt ? 'rgba(0,255,128,0.1)' : 'rgba(255,77,77,0.1)', color: agent.has_prompt ? '#00ff80' : '#ff4d4d' }}>{agent.has_prompt ? '✅ Prompt OK' : '❌ Sem Prompt'}</span>
                            <span style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.65rem', fontWeight: '700', background: agent.has_tools ? 'rgba(0,255,128,0.1)' : 'rgba(255,255,255,0.05)', color: agent.has_tools ? '#00ff80' : 'var(--text-muted)' }}>{agent.has_tools ? `🛠️ ${agent.tools.length} Tools` : '⚪ Sem Tools'}</span>
                          </div>
                          {agent.tools.length > 0 && (
                            <div style={{ marginTop: '10px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                              {agent.tools.map(t => (
                                <span key={t} style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.6rem', background: 'rgba(0,242,255,0.08)', color: 'var(--primary)', border: '1px solid rgba(0,242,255,0.2)' }}>{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div style={{ padding: '15px', background: 'rgba(255,255,255,0.02)', borderRadius: '10px', border: '1px solid var(--border)' }}>
                          <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '800', marginBottom: '8px', letterSpacing: '1px' }}>TASK BREAKDOWN</p>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                            <div style={{ textAlign: 'center' }}>
                              <p style={{ fontSize: '1.3rem', fontWeight: '900', color: '#00ff80' }}>{agent.task_summary.completed}</p>
                              <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Concluídas</p>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                              <p style={{ fontSize: '1.3rem', fontWeight: '900', color: 'var(--primary)' }}>{agent.task_summary.in_progress}</p>
                              <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Em Progresso</p>
                            </div>
                            <div style={{ textAlign: 'center' }}>
                              <p style={{ fontSize: '1.3rem', fontWeight: '900', color: '#f59e0b' }}>{agent.task_summary.open}</p>
                              <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>Abertas</p>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Tarefas do agente */}
                      {agent.tasks.length > 0 && (
                        <div style={{ marginBottom: '25px' }}>
                          <p style={{ fontSize: '0.7rem', color: 'var(--primary)', fontWeight: '900', marginBottom: '10px', letterSpacing: '2px' }}>📋 TAREFAS ATRIBUÍDAS</p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {agent.tasks.map((task, ti) => (
                              <div key={ti} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 120px 100px', alignItems: 'center', padding: '10px 15px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                <span style={{ fontSize: '0.7rem', color: 'var(--primary)', fontFamily: 'monospace', fontWeight: '700' }}>{task.id}</span>
                                <span style={{ fontSize: '0.8rem', color: '#e2e8f0' }}>{task.title}</span>
                                <StatusBadge status={task.status} />
                                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textAlign: 'right' }}>{task.priority || '—'}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Interações do agente */}
                      {agent.interactions.length > 0 && (
                        <div>
                          <p style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: '900', marginBottom: '10px', letterSpacing: '2px' }}>💬 ÚLTIMAS INTERAÇÕES ({agent.total_interactions} total)</p>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '300px', overflowY: 'auto' }}>
                            {agent.interactions.map((inter, ii) => (
                              <div key={ii} style={{ padding: '12px 15px', background: inter.type === 'execution' ? 'rgba(0,242,255,0.03)' : 'rgba(52,211,153,0.03)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', borderLeft: `3px solid ${inter.type === 'execution' ? 'var(--primary)' : '#34d399'}` }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                  <span style={{ fontSize: '0.65rem', fontWeight: '800', color: inter.type === 'execution' ? 'var(--primary)' : '#34d399' }}>{inter.type === 'execution' ? '⚡ Execução' : '📱 Telegram'}{inter.task_id ? ` • ${inter.task_id}` : ''}{inter.action ? ` • ${inter.action}` : ''}</span>
                                  <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>{inter.timestamp ? new Date(inter.timestamp).toLocaleString() : '—'}</span>
                                </div>
                                {inter.input && <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>📝 {inter.input.substring(0, 150)}{inter.input.length > 150 ? '...' : ''}</p>}
                                <p style={{ fontSize: '0.8rem', color: '#e2e8f0', lineHeight: '1.4' }}>{(inter.result || '').substring(0, 300)}{(inter.result || '').length > 300 ? '...' : ''}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {agent.tasks.length === 0 && agent.interactions.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '30px', opacity: 0.5 }}>
                          <p>⚠️ Agente sem tarefas e sem interações registradas.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Alertas: Tarefas sem agente e agentes órfãos */}
          {(qaReport.unassigned_tasks.length > 0 || qaReport.orphan_agents.length > 0) && (
            <div className="glass-card" style={{ borderLeft: '4px solid #ff4d4d' }}>
              <h3 style={{ color: '#ff4d4d', marginBottom: '15px', fontSize: '1rem' }}>⚠️ Alertas do Quality Inspector</h3>
              {qaReport.unassigned_tasks.length > 0 && (
                <div style={{ marginBottom: '15px' }}>
                  <p style={{ fontSize: '0.75rem', fontWeight: '800', color: '#f59e0b', marginBottom: '8px' }}>Tarefas sem agente atribuído:</p>
                  {qaReport.unassigned_tasks.map((t, i) => (
                    <div key={i} style={{ padding: '8px 12px', background: 'rgba(245,158,11,0.05)', borderRadius: '6px', marginBottom: '4px', fontSize: '0.8rem', color: '#e2e8f0' }}>
                      <span style={{ color: 'var(--primary)', fontFamily: 'monospace', marginRight: '10px' }}>{t.id}</span>
                      {t.title}
                    </div>
                  ))}
                </div>
              )}
              {qaReport.orphan_agents.length > 0 && (
                <div>
                  <p style={{ fontSize: '0.75rem', fontWeight: '800', color: '#ff4d4d', marginBottom: '8px' }}>Agentes com atividade mas não registrados:</p>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {qaReport.orphan_agents.map((name, i) => (
                      <span key={i} style={{ padding: '5px 12px', borderRadius: '8px', fontSize: '0.75rem', background: 'rgba(255,77,77,0.1)', color: '#ff4d4d', border: '1px solid rgba(255,77,77,0.3)' }}>{name}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      );
    }

    if (activeTab === 'DORA Metrics') {
      return (
        <div style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
            <div>
              <h2 className="title-grad" style={{ fontSize: '2rem', margin: 0 }}>Engineering Metrics</h2>
              <p style={{ color: 'var(--text-muted)' }}>DORA (DevOps Research and Assessment) Performance Dashboard</p>
            </div>
            <button onClick={fetchDoraData} className="glow-on-hover" style={{ padding: '10px 20px', borderRadius: '8px', border: '1px solid var(--primary)', background: 'rgba(0,242,255,0.1)', color: 'var(--primary)', cursor: 'pointer', fontWeight: 'bold' }}>
              RECARREGAR
            </button>
          </div>

          {!doraData ? (
            <div className="glass-card" style={{ textAlign: 'center', padding: '50px' }}>
              <p style={{ color: 'var(--primary)', fontSize: '1.2rem' }}>Loading DORA Telemetry...</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
              {/* Card 1: Deployment Frequency */}
              <div className="glass-card" style={{ borderTop: '3px solid #00f2ff', background: 'linear-gradient(145deg, rgba(0,242,255,0.05) 0%, rgba(10,14,26,0.9) 100%)' }}>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px' }}>🚀 Deployment Frequency</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#00f2ff', textShadow: '0 0 20px rgba(0,242,255,0.4)', marginBottom: '10px' }}>
                  {doraData.deployment_frequency}
                </div>
                <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Frequência de push/merge em produção nos últimos 30 dias.</p>
              </div>

              {/* Card 2: Lead Time for Changes */}
              <div className="glass-card" style={{ borderTop: '3px solid #f59e0b', background: 'linear-gradient(145deg, rgba(245,158,11,0.05) 0%, rgba(10,14,26,0.9) 100%)' }}>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px' }}>⏱️ Lead Time for Changes</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#f59e0b', textShadow: '0 0 20px rgba(245,158,11,0.4)', marginBottom: '10px' }}>
                  {doraData.lead_time}
                </div>
                <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Tempo médio entre o primeiro commit e o deploy (recibos recentes).</p>
              </div>

              {/* Card 3: MTTR */}
              <div className="glass-card" style={{ borderTop: '3px solid #34d399', background: 'linear-gradient(145deg, rgba(52,211,153,0.05) 0%, rgba(10,14,26,0.9) 100%)' }}>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px' }}>🔧 Mean Time To Recovery (MTTR)</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#34d399', textShadow: '0 0 20px rgba(52,211,153,0.4)', marginBottom: '10px' }}>
                  {doraData.mttr}
                </div>
                <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Tempo médio de recuperação de falhas ou incidentes abertos.</p>
              </div>

              {/* Card 4: Change Failure Rate */}
              <div className="glass-card" style={{ borderTop: '3px solid #ff4d4d', background: 'linear-gradient(145deg, rgba(255,77,77,0.05) 0%, rgba(10,14,26,0.9) 100%)' }}>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '15px' }}>⚠️ Change Failure Rate</h3>
                <div style={{ fontSize: '2.5rem', fontWeight: '900', color: '#ff4d4d', textShadow: '0 0 20px rgba(255,77,77,0.4)', marginBottom: '10px' }}>
                  {doraData.change_failure_rate}
                </div>
                <p style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.5)' }}>Porcentagem de deploys recentes que causaram falhas em produção.</p>
              </div>
            </div>
          )}

          <div style={{ marginTop: '30px' }} className="glass-card">
            <h3 style={{ fontSize: '1rem', color: 'var(--primary)', marginBottom: '15px' }}>DORA Telemetry Feed</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Total Deploys (30d): <strong style={{color: '#fff'}}>{doraData?.raw?.total_deploys_30d || 0}</strong> | 
              Incidentes Abertos: <strong style={{color: '#ff4d4d'}}>{doraData?.raw?.open_incidents || 0}</strong>
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '100px' }}>
        <h1 className="title-grad">{activeTab}</h1>
        <p style={{ color: 'var(--text-muted)' }}>This module is currently being optimized by the specialized agents.</p>
      </div>
    );
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
      const data = await response.json();
      if (data.status === 'authorized') {
        sessionStorage.setItem('flose_token', data.token);
        setToken(data.token);
        setIsAuthenticated(true);
      } else {
        setError(true);
        setTimeout(() => setError(false), 2000);
      }
    } catch (err) {
      console.error("Auth error", err);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('flose_token');
    setToken('');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="glass-card login-card">
          <h1 className="title-grad">Flose AI</h1>
          <p style={{ color: 'var(--text-muted)', marginBottom: '30px' }}>Secure Gateway</p>
          <form onSubmit={handleLogin}>
            <input 
              type="password" 
              placeholder="Enter Master Key" 
              className={`login-input ${error ? 'error' : ''}`}
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
            <button type="submit" className="login-button">ACCESS SYSTEM</button>
          </form>
          {error && <p style={{ color: 'var(--accent)', marginTop: '15px', fontSize: '0.8rem' }}>Invalid Credentials</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <div className="sidebar">
        <div className="logo" style={{ marginBottom: '60px' }}>
          <h1 className="title-grad">Flose IA</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Command Center v2.0</p>
        </div>
        
        <nav className="nav-menu">
          {['Dashboard', 'Cognitive Map', 'Task Manager', 'Agent Library', 'Pipeline', 'Marketplace', 'Quality Inspector', 'Broker', 'FinOps Guardian', 'DORA Metrics', 'Settings'].map(tab => (
            <div 
              key={tab}
              className={`nav-item ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </div>
          ))}
        </nav>

        <div className="user-profile" style={{ marginTop: 'auto', flexDirection: 'column', alignItems: 'stretch', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <div className="avatar">FF</div>
            <div className="user-info">
              <p className="user-name">Felipe Flose</p>
              <span className="badge badge-online">PRO Member</span>
            </div>
          </div>
          <button onClick={handleLogout} className="logout-button">LOGOUT</button>
        </div>
      </div>

      <main className="main-content">
        <header className="header" style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '1.8rem' }}>Welcome back, Director.</h2>
            <p style={{ color: 'var(--text-muted)' }}>The multi-agent system is operating within safe parameters.</p>
          </div>
          <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
            <button onClick={fetchData} className="refresh-btn">🔄 Refresh</button>
            <div className="system-time">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </header>

        {renderContent()}
        
        {/* TASK-06: Execution Preview Modal */}
        {executionPreview && (
          <div className="modal-overlay" style={{ zIndex: 3000 }}>
            <div className="glass-card modal-content" style={{ maxWidth: '500px', border: '1px solid var(--primary)', animation: 'scaleUp 0.3s ease' }}>
              <h2 className="title-grad" style={{ marginBottom: '15px' }}>🚀 Confirmar Execução Agente</h2>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '5px' }}>TAREFA:</p>
                <p style={{ fontWeight: 'bold', marginBottom: '15px' }}>{executionPreview.title}</p>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '5px' }}>RESPONSÁVEL:</p>
                    <p style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{executionPreview.responsible || 'Standard'}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '5px' }}>ESTIMATIVA CUSTO:</p>
                    <p style={{ color: '#f59e0b', fontWeight: 'bold' }}>~ 1.2k tokens ($0.001)</p>
                  </div>
                </div>
              </div>
              
              <div style={{ display: 'flex', gap: '15px' }}>
                <button className="refresh-btn" style={{ flex: 1 }} onClick={() => setExecutionPreview(null)}>CANCELAR</button>
                <button className="login-button" style={{ flex: 2, background: 'var(--primary)', color: '#000' }} onClick={() => {
                  setExecutingAgent(executionPreview.responsible);
                  handleExecute(executionPreview.id);
                  setExecutionPreview(null);
                }}>INICIAR AGORA</button>
              </div>
            </div>
          </div>
        )}
        
        {/* Agent Info Modal (Global) */}
        {viewingAgent && (
          <div className="modal-overlay" onClick={() => setViewingAgent(null)}>
            <div className="glass-card modal-content" onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                  <div className="avatar" style={{ width: '60px', height: '60px', fontSize: '1.5rem' }}>
                    {viewingAgent.agent_name.substring(0,2).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="title-grad" style={{ fontSize: '1.8rem' }}>{viewingAgent.agent_name}</h2>
                    <p style={{ color: 'var(--primary)', fontSize: '0.9rem' }}>{viewingAgent.purpose}</p>
                  </div>
                </div>
                <button onClick={() => setViewingAgent(null)} style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
              </div>
              
              <h4 style={{ color: 'var(--text-muted)', marginBottom: '10px', fontSize: '0.8rem', letterSpacing: '1px' }}>SYSTEM PROMPT / BEHAVIOR</h4>
              <div style={{ background: 'rgba(0,0,0,0.4)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)', maxHeight: '300px', overflowY: 'auto' }}>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: '#e0e0e0', lineHeight: '1.6' }}>
                  {viewingAgent.system_prompt}
                </pre>
              </div>
              
              {viewingAgent.tools && viewingAgent.tools.length > 0 && (
                <>
                  <h4 style={{ color: 'var(--text-muted)', margin: '20px 0 10px 0', fontSize: '0.8rem', letterSpacing: '1px' }}>AVAILABLE TOOLS</h4>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    {viewingAgent.tools.map(tool => (
                      <span key={tool} className="badge" style={{ background: 'var(--glass)', border: '1px solid var(--primary)', color: 'var(--primary)' }}>{tool}</span>
                    ))}
                  </div>
                </>
              )}
              
              <div style={{ marginTop: '30px', textAlign: 'right' }}>
                <button className="login-button" style={{ width: 'auto', padding: '10px 30px' }} onClick={() => setViewingAgent(null)}>CLOSE</button>
              </div>
            </div>
          </div>
        )}

        {/* Delivery Artifact Modal */}
        {viewingDelivery && (
          <div className="modal-overlay" onClick={() => setViewingDelivery(null)}>
            <div className="glass-card modal-content" style={{ maxWidth: '900px', width: '90%' }} onClick={e => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '15px' }}>
                <div>
                  <h2 className="title-grad">Agent Delivery Artifact</h2>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {viewingDelivery.task_id} | Agent: {viewingDelivery.agent}</p>
                </div>
                <button onClick={() => setViewingDelivery(null)} style={{ background: 'none', border: 'none', color: 'white', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
              </div>

              <div style={{ 
                background: '#09090b', 
                padding: '30px', 
                borderRadius: '12px', 
                border: '1px solid var(--border)', 
                maxHeight: '60vh', 
                overflowY: 'auto',
                boxShadow: 'inset 0 0 40px rgba(0,0,0,0.5)'
              }}>
                <pre style={{ 
                  whiteSpace: 'pre-wrap', 
                  fontSize: '0.95rem', 
                  color: viewingDelivery.error ? 'var(--accent)' : '#e2e8f0', 
                  lineHeight: '1.7',
                  fontFamily: '"JetBrains Mono", monospace'
                }}>
                  {viewingDelivery.error ? (
                    <div style={{ padding: '20px', border: '1px dashed var(--accent)', borderRadius: '8px' }}>
                      <h3 style={{ marginBottom: '10px' }}>⚠️ DATA RETRIEVAL ERROR</h3>
                      {viewingDelivery.error}
                      <p style={{ marginTop: '20px', fontSize: '0.8rem', opacity: 0.7 }}>
                        This usually happens if the agent execution logs were cleared or if the task was completed in a legacy session.
                      </p>
                    </div>
                  ) : (
                    viewingDelivery.result || "No data returned from agent execution."
                  )}
                </pre>
              </div>

              <div style={{ marginTop: '25px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {viewingDelivery.timestamp ? `Verified by Flose AI Platform • ${new Date(viewingDelivery.timestamp).toLocaleString()}` : "System Log Analysis"}
                </span>
                <button className="login-button" style={{ width: 'auto', padding: '12px 35px' }} onClick={() => setViewingDelivery(null)}>CLOSE</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
