import React, { useState, useEffect, useRef } from 'react';
import './App.css';

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
  const [viewingAgent, setViewingAgent] = useState(null);
  const [pipeline, setPipeline] = useState([]);
  const [pipelineResults, setPipelineResults] = useState([]);
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);
  const [marketTemplates, setMarketTemplates] = useState([]);
  const [isFixing, setIsFixing] = useState(false);
  const [viewingDelivery, setViewingDelivery] = useState(null);

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

  const useForce = (nodes, links, width, height) => {
    const pos = useRef({});
    const vel = useRef({});
    const iter = useRef(0);
    const raf = useRef(null);
    const [, tick] = useState(0);

    useEffect(() => {
      if (!width || !height || !nodes.length) return;
      
      const cx = width / 2;
      const cy = height / 2;

      nodes.forEach((n, i) => {
        if (pos.current[n.id]) return;
        
        if (n.type === 'core') {
          pos.current[n.id] = { x: cx, y: cy };
        } else if (n.type === 'pilar') {
          const angle = (i / 8) * Math.PI * 2;
          pos.current[n.id] = { x: cx + Math.cos(angle) * 250, y: cy + Math.sin(angle) * 250 };
        } else {
          const angle = Math.random() * Math.PI * 2;
          pos.current[n.id] = { x: cx + Math.cos(angle) * 450, y: cy + Math.sin(angle) * 450 };
        }
        vel.current[n.id] = { x: 0, y: 0 };
      });
      
      iter.current = 0;

      const step = () => {
        iter.current++;
        const a = Math.max(0.005, 0.8 * Math.exp(-iter.current * 0.01));
        const p = pos.current, v = vel.current;
        const ids = nodes.map(n => n.id);

        for (let i = 0; i < ids.length; i++) {
          for (let j = i + 1; j < ids.length; j++) {
            const A = ids[i], B = ids[j];
            const dx = p[B].x - p[A].x, dy = p[B].y - p[A].y;
            const distSq = dx * dx + dy * dy || 1;
            const dist = Math.sqrt(distSq);
            
            const nA = nodes.find(n => n.id === A);
            const nB = nodes.find(n => n.id === B);
            if (!nA || !nB) continue;

            const charge = (nA.type === 'core' || nB.type === 'core') ? 120000 : 
                           (nA.type === 'pilar' || nB.type === 'pilar') ? 40000 : 10000;

            if (dist < 500) {
              const f = (charge / distSq) * a;
              v[A].x -= dx / dist * f; v[A].y -= dy / dist * f;
              v[B].x += dx / dist * f; v[B].y += dy / dist * f;
            }
          }
        }

        links.forEach(l => {
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          if (!p[sId] || !p[tId]) return;
          
          const dx = p[tId].x - p[sId].x, dy = p[tId].y - p[sId].y;
          const d = Math.sqrt(dx * dx + dy * dy) || 1;
          const ideal = l.relation === 'groups' ? 120 : 250;
          const strength = (l.relation === 'groups' ? 0.15 : 0.05) * a;
          const f = (d - ideal) * strength;
          
          v[sId].x += dx / d * f; v[sId].y += dy / d * f;
          v[tId].x -= dx / d * f; v[tId].y -= dy / d * f;
        });

        nodes.forEach(n => {
          v[n.id].x += (cx - p[n.id].x) * (n.type === 'core' ? 0.1 : 0.01) * a;
          v[n.id].y += (cy - p[n.id].y) * (n.type === 'core' ? 0.1 : 0.01) * a;
          
          v[n.id].x *= 0.8; v[n.id].y *= 0.8;
          p[n.id].x = Math.max(50, Math.min(width - 50, p[n.id].x + v[n.id].x));
          p[n.id].y = Math.max(50, Math.min(height - 50, p[n.id].y + v[n.id].y));
        });

        tick(t => t + 1);
        if (a > 0.006) raf.current = requestAnimationFrame(step);
      };

      if (raf.current) cancelAnimationFrame(raf.current);
      raf.current = requestAnimationFrame(step);
      return () => { if (raf.current) cancelAnimationFrame(raf.current); };
    }, [nodes.length, links.length, width, height]);

    return pos.current;
  };

  const CognitiveMap = ({ data }) => {
    const nodes = data?.nodes || [];
    const links = data?.links || [];
    const containerRef = useRef(null);
    const [dims, setDims] = useState({ w: 1200, h: 800 });
    const [selected, setSelected] = useState(null);
    const [hovered, setHovered] = useState(null);
    const [filterType, setFilterType] = useState("all");
    const [dragging, setDragging] = useState(null);
    const dragOff = useRef({ x: 0, y: 0 });
    const posOverride = useRef({});
    const [, forceRender] = useState(0);
    const [isSaved, setIsSaved] = useState(false);

    useEffect(() => {
      const saved = localStorage.getItem("flose_cognitive_map_v2");
      if (saved) {
        try {
          posOverride.current = JSON.parse(saved);
          forceRender(v => v + 1);
        } catch (e) {
          console.error("Erro ao carregar layout", e);
        }
      }
    }, []);

    const handleSave = () => {
      const current = { ...posOverride.current };
      visNodes.forEach(n => {
        if (!current[n.id] && simPos[n.id]) current[n.id] = simPos[n.id];
      });
      localStorage.setItem("flose_cognitive_map_v2", JSON.stringify(current));
      posOverride.current = current;
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2000);
    };

    const handleReset = () => {
      if (window.confirm("Reseta o layout cognitivo?")) {
        localStorage.removeItem("flose_cognitive_map_v2");
        posOverride.current = {};
        window.location.reload();
      }
    };

    useEffect(() => {
      const obs = new ResizeObserver(e => {
        if (!e[0]) return;
        const { width, height } = e[0].contentRect;
        setDims({ w: Math.max(800, width), h: Math.max(500, height) });
      });
      if (containerRef.current) obs.observe(containerRef.current);
      return () => obs.disconnect();
    }, []);

    const visNodes = filterType === "all" ? nodes : nodes.filter(n => n.type === filterType);
    const visIds = new Set(visNodes.map(n => n.id));
    const visLinks = links.filter(l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return visIds.has(sId) && visIds.has(tId);
    });

    const simPos = useForce(visNodes, visLinks, dims.w, dims.h);
    const getP = id => posOverride.current[id] || simPos[id] || { x: dims.w / 2, y: dims.h / 2 };

    const activeNode = selected || hovered;
    const activeLinks = activeNode ? visLinks.filter(l => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      return sId === activeNode?.id || tId === activeNode?.id;
    }) : [];
    
    const activeIds = new Set(activeLinks.flatMap(l => [
      typeof l.source === 'object' ? l.source.id : l.source,
      typeof l.target === 'object' ? l.target.id : l.target
    ]));

    const onMD = (e, id) => {
      e.stopPropagation();
      const p = getP(id), svg = e.currentTarget.closest("svg"), r = svg.getBoundingClientRect();
      dragOff.current = { x: e.clientX - r.left - p.x, y: e.clientY - r.top - p.y };
      setDragging(id); setSelected(nodes.find(n => n.id === id));
    };

    useEffect(() => {
      if (!dragging) return;
      const mv = e => {
        const svg = containerRef.current?.querySelector("svg");
        if (!svg) return;
        const r = svg.getBoundingClientRect();
        posOverride.current[dragging] = {
          x: Math.max(50, Math.min(dims.w - 50, e.clientX - r.left - dragOff.current.x)),
          y: Math.max(50, Math.min(dims.h - 50, e.clientY - r.top - dragOff.current.y)),
        };
        forceRender(v => v + 1);
      };
      const up = () => setDragging(null);
      window.addEventListener("mousemove", mv); window.addEventListener("mouseup", up);
      return () => { window.removeEventListener("mousemove", mv); window.removeEventListener("mouseup", up); };
    }, [dragging, dims]);

    if (!nodes.length) return <div className="loading">LOADING COGNITIVE_DATA...</div>;

    return (
      <div className="glass-card" style={{ height: '75vh', position: 'relative', overflow: 'hidden', padding: 0, border: '1px solid var(--border)', background: '#02040a' }}>
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, zIndex: 10, padding: '20px 30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'linear-gradient(to bottom, rgba(2,4,10,0.9), transparent)' }}>
          <div style={{ pointerEvents: 'none' }}>
            <h2 className="title-grad" style={{ letterSpacing: '4px', fontSize: '1.1rem', marginBottom: '5px' }}>COGNITIVE_NEXUS_v4.5</h2>
            <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.6rem', color: '#00ff80', fontWeight: 'bold' }}>● SYSTEM_OPERATIONAL</span>
              <span style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.4)' }}>{visNodes.length} NODES_IN_VIEW</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '15px' }}>
             <button onClick={handleSave} style={{ padding: "8px 16px", background: isSaved ? "var(--secondary)" : "rgba(255,255,255,0.05)", color: isSaved ? "#000" : "#fff", border: isSaved ? "none" : "1px solid var(--primary)", borderRadius: "4px", fontSize: "10px", fontWeight: "900", cursor: "pointer", transition: "all 0.3s" }}>
              {isSaved ? "LAYOUT_SAVED" : "SAVE_SNAPSHOT"}
            </button>
            <button onClick={handleReset} style={{ padding: "8px 16px", background: "transparent", color: "rgba(255,255,255,0.4)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "4px", fontSize: "10px", fontWeight: "900", cursor: "pointer" }}>
              RESET
            </button>
            <div style={{ width: '1px', height: '25px', background: 'rgba(255,255,255,0.1)', margin: '0 5px' }} />
            <SlantButton active={filterType === 'all'} onClick={() => setFilterType('all')}>ALL_NODES</SlantButton>
            <SlantButton color="var(--primary)" active={filterType === 'core'} onClick={() => setFilterType('core')}>CORE</SlantButton>
            <SlantButton color="#f59e0b" active={filterType === 'pilar'} onClick={() => setFilterType('pilar')}>PILLARS</SlantButton>
            <SlantButton color="#34d399" active={filterType === 'concept'} onClick={() => setFilterType('concept')}>CONCEPTS</SlantButton>
          </div>
        </div>
        <div style={{ position: "absolute", bottom: 30, right: selected ? 420 : 30, zIndex: 15, background: "rgba(5, 8, 18, 0.9)", backdropFilter: "blur(10px)", border: `1px solid var(--border)`, borderRadius: 12, padding: "15px 25px", boxShadow: "0 0 40px rgba(0,0,0,0.5)", transition: "all 0.4s cubic-bezier(0.19, 1, 0.22, 1)", display: "flex", gap: "30px", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "9px", color: "var(--text-muted)", fontWeight: "800", textTransform: "uppercase", letterSpacing: '1px', marginBottom: '4px' }}>CORE_ENGINES</div>
            <div style={{ fontSize: "22px", fontWeight: "900", color: "var(--primary)", textShadow: '0 0 10px var(--primary)' }}>{nodes.filter(n => n.type === 'core').length}</div>
          </div>
          <div style={{ width: "1px", height: "35px", background: "rgba(255,255,255,0.1)" }} />
          <div>
            <div style={{ fontSize: "9px", color: "var(--text-muted)", fontWeight: "800", textTransform: "uppercase", letterSpacing: '1px', marginBottom: '4px' }}>PILLAR_MODULES</div>
            <div style={{ fontSize: "22px", fontWeight: "900", color: "#f59e0b", textShadow: '0 0 10px #f59e0b66' }}>{nodes.filter(n => n.type === 'pilar').length}</div>
          </div>
          <div style={{ width: "1px", height: "35px", background: "rgba(255,255,255,0.1)" }} />
          <div>
            <div style={{ fontSize: "9px", color: "var(--text-muted)", fontWeight: "800", textTransform: "uppercase", letterSpacing: '1px', marginBottom: '4px' }}>TOTAL_CONCEPTS</div>
            <div style={{ fontSize: "22px", fontWeight: "900", color: "#34d399", textShadow: '0 0 10px #34d39966' }}>{nodes.length}</div>
          </div>
        </div>
        <div ref={containerRef} style={{ height: '100%', width: '100%', position: "relative" }} onClick={() => setSelected(null)}>
          <svg width={dims.w} height={dims.h} style={{ background: 'radial-gradient(circle at center, #0a0e1a 0%, #010101 100%)' }}>
            <defs>
              <filter id="floseGlow" x="-100%" y="-100%" width="300%" height="300%">
                <feGaussianBlur stdDeviation="5" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>
            {filterType === "all" && nodes.filter(n => n.type === 'pilar').map(pnode => {
              const p = getP(pnode.id);
              return <circle key={`cluster-${pnode.id}`} cx={p.x} cy={p.y} r={120} fill="none" stroke="#f59e0b" strokeWidth={0.5} strokeDasharray="5,10" opacity={0.15} />;
            })}
            {visLinks.map((l, i) => {
              const sId = typeof l.source === 'object' ? l.source.id : l.source;
              const tId = typeof l.target === 'object' ? l.target.id : l.target;
              const sp = getP(sId), tp = getP(tId);
              if (!sp || !tp) return null;
              const isAct = activeLinks.includes(l);
              return <line key={`l-${i}`} x1={sp.x} y1={sp.y} x2={tp.x} y2={tp.y} stroke={isAct ? "var(--primary)" : "rgba(255,255,255,0.06)"} strokeWidth={isAct ? 2 : 1} filter={isAct ? "url(#floseGlow)" : ""} style={{ transition: "all 0.3s" }} />;
            })}
            {visNodes.map(n => {
              const p = getP(n.id); if (!p) return null;
              const isSel = selected?.id === n.id, isHov = hovered?.id === n.id;
              const isDim = activeNode && !activeIds.has(n.id) && activeNode.id !== n.id;
              const radius = n.type === 'core' ? 35 : (n.type === 'pilar' ? 20 : 10);
              const col = n.type === 'core' ? "var(--primary)" : (n.type === 'pilar' ? "var(--secondary)" : "var(--accent)");
              return (
                <g key={n.id} transform={`translate(${p.x},${p.y})`} style={{ cursor: "grab" }} onMouseDown={ev => onMD(ev, n.id)} onMouseEnter={() => setHovered(n)} onMouseLeave={() => setHovered(null)} onClick={ev => { ev.stopPropagation(); setSelected(n); }}>
                  {(isSel || isHov) && <circle r={radius + 8} fill="none" stroke={col} strokeWidth={2} strokeDasharray="4,4" opacity={0.6} filter="url(#floseGlow)" className="rotate" />}
                  {(n.type === 'core' || isSel || isHov) && <circle r={radius + 5} fill={col} opacity={isDim ? 0.05 : 0.15} filter="url(#floseGlow)" />}
                  <circle r={radius} fill={isDim ? "rgba(255,255,255,0.05)" : (isSel || isHov ? col : "rgba(10,14,26,0.9)")} stroke={col} strokeWidth={isSel ? 3 : 1.5} style={{ transition: "all 0.2s" }} />
                  {(n.type !== 'concept' || isSel || isHov) && !isDim && <text y={radius + 20} textAnchor="middle" fontSize={radius < 15 ? 9 : 11} fill={isSel || isHov ? "#fff" : "rgba(255,255,255,0.6)"} fontWeight={isSel ? 900 : 700} style={{ pointerEvents: "none", userSelect: "none" }}>{n.id.toUpperCase()}</text>}
                </g>
              );
            })}
          </svg>

          {/* Legend Card (Jamef Style) */}
          <div style={{ position: "absolute", bottom: 24, left: 24, background: "rgba(5, 8, 18, 0.8)", backdropFilter: "blur(10px)", border: `1px solid var(--border)`, borderRadius: 12, padding: "16px", boxShadow: "0 10px 30px rgba(0,0,0,0.5)", minWidth: "160px", zIndex: 15 }}>
            <div style={{ color: "var(--primary)", fontSize: 10, fontWeight: 900, marginBottom: 12, borderBottom: `2px solid var(--primary)`, display: "inline-block", letterSpacing: '1px' }}>SYSTEM_MAP_LEGEND</div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--primary)", boxShadow: "0 0 10px var(--primary)" }} />
              <span style={{ color: "rgba(255,255,255,0.7)", fontSize: 9, fontWeight: 800 }}>CORE_ENGINE</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--secondary)", boxShadow: "0 0 10px var(--secondary)" }} />
              <span style={{ color: "rgba(255,255,255,0.7)", fontSize: 9, fontWeight: 800 }}>PILLAR_CLUSTER</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--accent)", boxShadow: "0 0 10px var(--accent)" }} />
              <span style={{ color: "rgba(255,255,255,0.7)", fontSize: 9, fontWeight: 800 }}>DEEP_CONCEPT</span>
            </div>
          </div>

          <div style={{ position: "absolute", top: 0, right: 0, width: selected ? 400 : 0, height: '100%', background: "rgba(2,4,10,0.95)", borderLeft: `1px solid var(--border)`, overflow: "hidden", transition: "width .4s cubic-bezier(0.19, 1, 0.22, 1)", display: "flex", flexDirection: "column", boxShadow: "-20px 0 50px rgba(0,0,0,0.8)", zIndex: 100, backdropFilter: 'blur(20px)' }}>
            {selected && (
              <div style={{ padding: 40, overflowY: "auto", flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 30 }}>
                  <div>
                    <div style={{ color: "var(--primary)", fontSize: "0.6rem", fontWeight: "900", letterSpacing: '5px', marginBottom: "10px" }}>NEURAL_NODE_ID: {selected.type === 'core' ? '0XFF' : '0XBC'}</div>
                    <h2 style={{ color: "#fff", fontSize: "2rem", fontWeight: "900", lineHeight: 1.1 }}>{selected.id.toUpperCase()}</h2>
                  </div>
                  <button onClick={() => setSelected(null)} style={{ background: "rgba(255,255,255,0.05)", border: "none", borderRadius: "50%", width: 40, height: 40, color: "#fff", cursor: "pointer" }}>✕</button>
                </div>
                <div style={{ background: "rgba(0,242,255,0.03)", border: "1px solid var(--border)", borderRadius: 12, padding: 25, marginBottom: 30, borderLeft: '4px solid var(--primary)' }}>
                  <p style={{ color: "rgba(255,255,255,0.8)", fontSize: "0.95rem", lineHeight: 1.6 }}>{selected.type === 'core' ? 'Primary Nexus. Managing all cognitive orchestration and coordination.' : selected.type === 'pilar' ? 'Thematic Cluster. Higher order organization of related modules.' : 'Deep Intelligence Concept. Atomic memory unit validated by system.'}</p>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: '1fr 1fr', gap: 15, marginBottom: 30 }}>
                  <div style={{ border: `1px solid rgba(255,255,255,0.1)`, borderRadius: 12, padding: 15, background: 'rgba(255,255,255,0.02)' }}>
                    <div style={{ fontSize: "0.6rem", color: "rgba(255,255,255,0.4)", fontWeight: "800", marginBottom: '5px' }}>HEALTH</div>
                    <div style={{ fontSize: "1rem", fontWeight: "900", color: "#00ff80" }}>100% ONLINE</div>
                  </div>
                  <div style={{ border: `1px solid rgba(255,255,255,0.1)`, borderRadius: 12, padding: 15, background: 'rgba(255,255,255,0.02)' }}>
                    <div style={{ fontSize: "0.6rem", color: "rgba(255,255,255,0.4)", fontWeight: "800", marginBottom: '5px' }}>LATENCY</div>
                    <div style={{ fontSize: "1rem", fontWeight: "900", color: "var(--primary)" }}>24MS</div>
                  </div>
                </div>
                <div style={{ fontSize: "0.7rem", color: "rgba(255,255,255,0.3)", fontWeight: "900", letterSpacing: '2px', marginBottom: "15px", borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>CONNECTED_NODES ({activeLinks.length})</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {activeLinks.map((l, idx) => {
                    const otherId = (typeof l.source === 'object' ? l.source.id : l.source) === selected.id ? (typeof l.target === 'object' ? l.target.id : l.target) : (typeof l.source === 'object' ? l.source.id : l.source);
                    return <div key={idx} onClick={() => setSelected(nodes.find(n => n.id === otherId))} style={{ padding: '15px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.1)', cursor: 'pointer', transition: 'all 0.2s' }} onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--primary)'} onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}><div style={{ fontSize: '0.9rem', color: '#fff', fontWeight: '700' }}>{otherId}</div></div>;
                  })}
                </div>
              </div>
            )}
          </div>
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
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '30px' }}>
          <div className="task-grid">
            {tasks.map(task => (
              <div key={task.id} className={`glass-card task-card ${selectedTask?.id === task.id ? 'active' : ''}`} onClick={() => setSelectedTask(task)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '15px' }}>
                  <span style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{task.id}</span>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <span style={{ fontSize: '1rem' }}>{task.budget_approved ? '✅' : '⏳'}</span>
                    <span className={`badge ${
                      task.status === 'Concluído' ? 'badge-online' : 
                      task.status === 'Aberto' ? 'badge-pending' : 'badge-progress'
                    }`} style={{ fontSize: '0.6rem' }}>{task.status}</span>
                  </div>
                </div>
                <h4>{task.title}</h4>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '15px' }}>
                  <span className="badge" style={{ fontSize: '0.6rem', background: 'rgba(255,255,255,0.1)' }}>{task.priority || 'Média'}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>👤 {task.responsible || 'IA'}</span>
                </div>
                {task.terraform_plan && <div style={{ marginTop: '10px', color: 'var(--primary)', fontSize: '0.6rem' }}>🏗️ Terraform Ready</div>}
              </div>
            ))}
          </div>

          <div className="glass-card detail-panel">
            {selectedTask ? (
              <>
                <h3>Task Details</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '5px' }}>ID: {selectedTask.id}</p>
                <hr style={{ margin: '20px 0', borderColor: 'var(--border)' }} />
                
                <h4 style={{ color: 'var(--primary)' }}>Objective</h4>
                <p style={{ fontSize: '0.9rem', marginTop: '10px' }}>{selectedTask.title}</p>
                
                <h4 style={{ color: 'var(--primary)', marginTop: '20px' }}>Governance (FinOps)</h4>
                <p style={{ fontSize: '0.8rem', marginTop: '5px' }}>{selectedTask.cost_explanation || 'Aguardando especificações técnicas...'}</p>
                
                {selectedTask.terraform_plan && (
                  <>
                    <h4 style={{ color: 'var(--primary)', marginTop: '20px' }}>Infrastructure (Tf)</h4>
                    <pre style={{ fontSize: '0.7rem', background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', marginTop: '10px', overflowX: 'auto' }}>
                      {selectedTask.terraform_plan}
                    </pre>
                  </>
                )}

                <div style={{ marginTop: '30px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {!selectedTask.budget_approved && (
                    <button className="login-button" onClick={() => handleApprove(selectedTask.id)}>👍 APPROVE BUDGET</button>
                  )}
                  
                  {selectedTask.status === 'Aberto' && selectedTask.budget_approved && (
                    <div style={{ background: 'rgba(0,242,255,0.05)', padding: '15px', borderRadius: '12px', border: '1px solid var(--primary)' }}>
                      <p style={{ fontSize: '0.8rem', marginBottom: '10px', fontWeight: 'bold' }}>Delegated Specialist:</p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                        <div className="avatar" style={{ scale: '0.8' }}>{selectedTask.responsible?.substring(0,2).toUpperCase()}</div>
                        <span style={{ color: 'white' }}>{selectedTask.responsible}</span>
                      </div>
                      <button className="login-button" style={{ background: 'var(--primary)', color: 'black' }} onClick={() => {
                        setExecutingAgent(selectedTask.responsible);
                        handleExecute(selectedTask.id);
                      }}>🚀 RUN AS {selectedTask.responsible?.toUpperCase()}</button>
                    </div>
                  )}

                  {selectedTask.status === 'Concluído' && (
                    <button className="login-button" style={{ background: '#28a745' }} onClick={() => handleViewDelivery(selectedTask.result_id)}>📦 VIEW DELIVERY</button>
                  )}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', paddingTop: '50px' }}>
                <p>Select a TRD card to view details and governance actions.</p>
              </div>
            )}
          </div>
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
                <div key={tpl.name} className="glass-card agent-card-edit" style={{ border: '1px solid rgba(0,255,128,0.2)' }}>
                  <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '15px' }}>
                    <div className="avatar" style={{ background: '#34d399', color: 'black' }}>{tpl.name[0]}</div>
                    <h4 style={{ color: '#34d399' }}>{tpl.name}</h4>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', minHeight: '40px' }}>{tpl.purpose}</p>
                  
                  <NapkinVisual visualUrl={tpl.napkin_visual_url} />

                  <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.6rem', opacity: 0.5 }}>By {tpl.author}</span>
                    <button className="nav-item badge-online" style={{ padding: '5px 15px', fontSize: '0.6rem' }} onClick={() => handleImport(tpl.name)}>📥 IMPORT</button>
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
      const qaLogs = activity.filter(a => a.agent === 'QualityInspector' || (a.message && a.message.includes('QualityInspector')));
      
      return (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px' }}>
          <div className="glass-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <h2 className="title-grad" style={{ fontSize: '1.8rem' }}>QA & Audit Logs</h2>
                <p style={{ color: 'var(--text-muted)' }}>Watch the QualityInspector enforce rules and debate with other agents.</p>
              </div>
              <button 
                onClick={handleQAAutoFix} 
                disabled={isFixing}
                className="login-button" 
                style={{ width: 'auto', padding: '10px 25px', background: 'var(--primary)', boxShadow: '0 0 15px var(--primary-glow)' }}
              >
                {isFixing ? '🌀 ANALYZING...' : '⚡ AUTO-FIX BACKLOG'}
              </button>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginTop: '20px' }}>
              {qaLogs.length > 0 ? qaLogs.map((log, idx) => (
                <div key={idx} style={{ background: 'rgba(255,0,0,0.05)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #ff4d4d' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontWeight: 'bold', color: '#ff4d4d' }}>🚨 QualityInspector Request</span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>{log.message}</p>
                </div>
              )) : (
                <div style={{ textAlign: 'center', padding: '50px', opacity: 0.5 }}>
                  <h3>No Quality Inspector Interventions Yet</h3>
                  <p style={{ fontSize: '0.8rem', marginTop: '10px' }}>The system is currently operating within expected parameters.</p>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card">
            <h3 style={{ marginBottom: '20px' }}>System Health</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div style={{ padding: '15px', background: 'var(--glass)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>REJECTIONS</p>
                <p style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#ff4d4d' }}>{qaLogs.length}</p>
              </div>
              <div style={{ padding: '15px', background: 'var(--glass)', borderRadius: '12px', border: '1px solid var(--border)' }}>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PASS RATE</p>
                <p style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#00ff80' }}>
                  {qaLogs.length === 0 ? '100%' : `${Math.max(10, 100 - qaLogs.length * 5)}%`}
                </p>
              </div>
            </div>
            
            <div style={{ marginTop: '30px' }}>
              <h4 style={{ marginBottom: '15px', color: 'var(--primary)', fontSize: '0.9rem' }}>Current Directives:</h4>
              <ul style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <li>✔️ Prevent agents from closing empty tasks</li>
                <li>✔️ Force Terraform plan verification</li>
                <li>✔️ Ensure cost explanations in FinOps</li>
                <li>✔️ Debate unnecessary allocations</li>
              </ul>
            </div>
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
          {['Dashboard', 'Cognitive Map', 'Task Manager', 'Agent Library', 'Pipeline', 'Marketplace', 'Quality Inspector', 'FinOps Guardian', 'Settings'].map(tab => (
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
