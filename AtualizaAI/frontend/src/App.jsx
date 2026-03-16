import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(localStorage.getItem('flose_auth') === 'true');
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

  // Buscar dados reais da API
  const fetchData = async () => {
    try {
      const token = "flosetoken_secure_v2";
      const [statsRes, graphRes, tasksRes, activityRes, agentsRes] = await Promise.all([
        fetch(`/api/stats?token=${token}`),
        fetch(`/api/graph?token=${token}`),
        fetch(`/api/tasks?token=${token}`),
        fetch(`/api/activity?token=${token}`),
        fetch(`/api/agents?token=${token}`)
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

      const marketRes = await fetch(`/api/marketplace?token=${token}`);
      const marketD = await marketRes.json();
      if (!marketD.error) setMarketTemplates(marketD);
    } catch (err) {
      console.error("Fetch error", err);
    }
  };

  const handleApprove = async (taskId) => {
    const token = "flosetoken_secure_v2";
    await fetch(`/api/tasks/approve?task_id=${taskId}&token=${token}`, { method: 'POST' });
    fetchData();
  };

  const handleExecute = async (taskId) => {
    if (!executingAgent) return alert("Selecione um agente!");
    const token = "flosetoken_secure_v2";
    const res = await fetch(`/api/tasks/execute?task_id=${taskId}&agent_name=${executingAgent}&token=${token}`, { method: 'POST' });
    const data = await res.json();
    alert(data.status === 'success' ? "Tarefa executada com sucesso!" : "Erro: " + data.error);
    fetchData();
  };

  const handleViewDelivery = async (resultId) => {
    const token = "flosetoken_secure_v2";
    const res = await fetch(`/api/tasks/delivery/${resultId}?token=${token}`);
    const data = await res.json();
    alert("Resultado:\n\n" + data.result);
  };

  const handleAgentQuery = async (query) => {
    const token = "flosetoken_secure_v2";
    const res = await fetch(`/api/agents/chat?token=${token}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    alert("🤖 Response: " + data.response);
    fetchData();
  };

  const handleExport = async (name) => {
    const token = "flosetoken_secure_v2";
    const res = await fetch(`/api/marketplace/export/${name}?token=${token}`, { method: 'POST' });
    const data = await res.json();
    alert(data.status === 'success' ? "Agente exportado como template!" : "Erro ao exportar");
    fetchData();
  };

  const handleImport = async (templateName) => {
    const token = "flosetoken_secure_v2";
    const res = await fetch(`/api/marketplace/import?token=${token}`, { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template_name: templateName })
    });
    const data = await res.json();
    alert(data.status === 'success' ? "Template importado com sucesso!" : "Erro ao importar");
    fetchData();
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 30000); 
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Hook de Física Avançado v4
  const NapkinVisual = ({ visualId }) => {
    const [imgUrl, setImgUrl] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const fetchVisual = async () => {
        if (!visualId) return;
        try {
          const token = "flosetoken_secure_v2";
          const res = await fetch(`/api/marketplace/visual/${visualId}?token=${token}`);
          const data = await res.json();
          // Based on exploration, Napkin returns something like { "files": [ { "url": "..." } ] }
          if (data && data.files && data.files.length > 0) {
            setImgUrl(data.files[0].url);
          }
        } catch (e) {
          console.error("Napkin fetch error", e);
        } finally {
          setLoading(false);
        }
      };
      fetchVisual();
    }, [visualId]);

    if (!visualId) return null;
    if (loading) return <div style={{ fontSize: '0.6rem', opacity: 0.5 }}>🎨 Generating visual...</div>;
    if (!imgUrl) return <div style={{ fontSize: '0.6rem', opacity: 0.3 }}>No visual available</div>;

    return (
      <div style={{ marginTop: '15px', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)' }}>
        <img src={imgUrl} alt="Agent logic diagram" style={{ width: '100%', display: 'block' }} />
      </div>
    );
  };

  const useForce = (nodes, links, width, height) => {
    const [positions, setPositions] = useState({});
    const simulationRef = useRef(null);

    useEffect(() => {
      const safeNodes = nodes || [];
      const safeLinks = links || [];
      if (!safeNodes.length) return;
      
      const pos = {};
      const vel = {};
      const cx = width / 2;
      const cy = height / 2;

      // Inicialização inteligente baseada em hierarquia
      safeNodes.forEach((n, i) => {
        if (n.type === 'core') {
          pos[n.id] = { x: cx, y: cy };
        } else if (n.type === 'pilar') {
          const angle = (i / 10) * Math.PI * 2;
          pos[n.id] = { x: cx + Math.cos(angle) * 180, y: cy + Math.sin(angle) * 180 };
        } else {
          const angle = Math.random() * Math.PI * 2;
          pos[n.id] = { x: cx + Math.cos(angle) * 350, y: cy + Math.sin(angle) * 350 };
        }
        vel[n.id] = { x: 0, y: 0 };
      });

      let iteration = 0;
      const step = () => {
        iteration++;
        const alpha = Math.max(0.01, 1.0 * Math.exp(-iteration * 0.012));
        
        // 1. Repulsão Global (Muito maior para evitar overlap)
        safeNodes.forEach(n1 => {
          safeNodes.forEach(n2 => {
            if (n1.id === n2.id) return;
            const dx = pos[n2.id].x - pos[n1.id].x;
            const dy = pos[n2.id].y - pos[n1.id].y;
            const distSq = dx * dx + dy * dy || 1;
            const dist = Math.sqrt(distSq);
            
            // Repulsão variável: Pilares se repelem mais
            const charge = (n1.type === 'pilar' || n2.type === 'pilar') ? 15000 : 5000;
            if (dist < 450) {
              const force = (charge / distSq) * alpha;
              vel[n1.id].x -= (dx / dist) * force;
              vel[n1.id].y -= (dy / dist) * force;
            }
          });
        });

        // 2. Atração de Links
        safeLinks.forEach(l => {
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          const s = pos[sId];
          const t = pos[tId];
          if (!s || !t) return;
          
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          
          // Distância ideal por tipo de relação
          let ideal = 140;
          if (l.relation === 'defined_by') ideal = 200;
          if (l.relation === 'groups') ideal = 100;

          const strength = (l.relation === 'groups' ? 0.2 : 0.1) * alpha;
          const force = (dist - ideal) * strength;
          
          vel[sId].x += (dx / dist) * force;
          vel[sId].y += (dy / dist) * force;
          vel[tId].x -= (dx / dist) * force;
          vel[tId].y -= (dy / dist) * force;
        });

        // 3. Gravidade e Centralização
        safeNodes.forEach(n => {
          if (n.type === 'core') {
            vel[n.id].x += (cx - pos[n.id].x) * 0.25 * alpha;
            vel[n.id].y += (cy - pos[n.id].y) * 0.25 * alpha;
          } else {
            vel[n.id].x += (cx - pos[n.id].x) * 0.015 * alpha;
            vel[n.id].y += (cy - pos[n.id].y) * 0.015 * alpha;
          }
          
          pos[n.id].x += vel[n.id].x;
          pos[n.id].y += vel[n.id].y;
          
          vel[n.id].x *= 0.75;
          vel[n.id].y *= 0.75;
        });

        setPositions({...pos});
        if (alpha > 0.01) simulationRef.current = requestAnimationFrame(step);
      };

      simulationRef.current = requestAnimationFrame(step);
      return () => cancelAnimationFrame(simulationRef.current);
    }, [nodes.length, links.length, width, height]);

    return positions;
  };

  const CognitiveMap = ({ data }) => {
    const nodes = data?.nodes || [];
    const links = data?.links || [];
    const [viewBox, setViewBox] = useState({ x: 0, y: 0, w: 1200, h: 800 });
    const pos = useForce(nodes, links, 1200, 800);
    
    if (!nodes.length) {
      return (
        <div className="glass-card" style={{ height: '75vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="loading-spinner"></div>
          <p style={{ marginLeft: '15px', color: 'var(--primary)', letterSpacing: '2px' }}>LOADING COGNITIVE NEURONS...</p>
        </div>
      );
    }

    return (
      <div className="glass-card graph-container" style={{ height: '75vh', position: 'relative', overflow: 'hidden', padding: 0, border: '1px solid rgba(0, 242, 255, 0.2)' }}>
        {/* Top Header Overlay */}
        <div style={{ position: 'absolute', top: '25px', left: '30px', zIndex: 10, pointerEvents: 'none' }}>
          <h2 className="title-grad" style={{ letterSpacing: '4px', fontSize: '1.2rem', marginBottom: '8px', textShadow: '0 0 20px rgba(0,242,255,0.4)' }}>COGNITIVE_NEXUS_v4.5</h2>
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.65rem', color: '#00ff80', fontWeight: 'bold' }}>● SYSTEM_ONLINE</span>
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{nodes.length} KNOWLEDGE_NODES</span>
          </div>
        </div>

        {/* Legend */}
        <div style={{ position: 'absolute', bottom: '25px', right: '30px', zIndex: 10, display: 'flex', gap: '20px', background: 'rgba(0,0,0,0.5)', padding: '10px 25px', borderRadius: '40px', border: '1px solid var(--border)', backdropFilter: 'blur(10px)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary)', boxShadow: '0 0 10px var(--primary)' }}></div>
            <span style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.7)' }}>Core Intelligence</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b', boxShadow: '0 0 10px #f59e0b' }}></div>
            <span style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.7)' }}>Pillar Cluster</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }}></div>
            <span style={{ fontSize: '0.6rem', color: 'rgba(255,255,255,0.7)' }}>Deep Concept</span>
          </div>
        </div>

        <div style={{ height: '100%', width: '100%' }}>
          <svg width="100%" height="100%" viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`} style={{ background: 'radial-gradient(circle at center, #0a0e1a 0%, #02040a 100%)' }}>
            <defs>
              <filter id="neon-glow" x="-100%" y="-100%" width="300%" height="300%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Radiant Circles */}
            <circle cx="600" cy="400" r="180" fill="none" stroke="rgba(0,242,255,0.04)" strokeWidth="1" strokeDasharray="10 20" />
            <circle cx="600" cy="400" r="350" fill="none" stroke="rgba(0,242,255,0.02)" strokeWidth="1" strokeDasharray="5 15" />

            {/* Links - Highly Visible Neon */}
            {links.map((link, i) => {
              const sId = typeof link.source === 'object' ? link.source.id : link.source;
              const tId = typeof link.target === 'object' ? link.target.id : link.target;
              const s = pos[sId];
              const t = pos[tId];
              if (!s || !t) return null;
              
              const isHigh = hoveredNode && (hoveredNode.id === sId || hoveredNode.id === tId);
              
              return (
                <g key={`l-grp-${i}`}>
                   <line 
                    x1={s.x} y1={s.y} x2={t.x} y2={t.y} 
                    stroke="var(--primary)" 
                    strokeOpacity={isHigh ? 0.7 : 0.08} 
                    strokeWidth={isHigh ? 3 : 1.5} 
                    filter={isHigh ? "url(#neon-glow)" : ""}
                    style={{ transition: 'all 0.4s ease' }}
                  />
                </g>
              );
            })}

            {/* Nodes */}
            {nodes.map(node => {
              const p = pos[node.id];
              if (!p) return null;
              
              const isCore = node.type === 'core';
              const isPilar = node.type === 'pilar';
              const isSel = selectedNode && selectedNode.id === node.id;
              const isHov = hoveredNode && hoveredNode.id === node.id;
              
              // CRITICAL FIX: Only show labels for Core & Pillars by default to avoid mess
              const showLabel = isCore || isPilar || isHov || isSel;

              return (
                <g 
                  key={node.id} 
                  transform={`translate(${p.x}, ${p.y})`} 
                  className={`graph-node ${isCore ? 'core' : ''}`}
                  onMouseEnter={() => setHoveredNode(node)} 
                  onMouseLeave={() => setHoveredNode(null)} 
                  onClick={() => setSelectedNode(node)}
                >
                  {/* Node Body with Glow */}
                  <circle 
                    r={isCore ? 30 : (isPilar ? 15 : 7)} 
                    fill={isCore ? 'var(--primary)' : (isPilar ? '#f59e0b' : '#34d399')}
                    fillOpacity={isHov || isSel ? 1 : 0.8}
                    stroke={isSel ? '#fff' : (isHov ? 'var(--primary)' : 'rgba(255,255,255,0.05)')}
                    strokeWidth={isSel || isHov ? 3 : 1}
                    filter={isCore || isHov || isSel ? "url(#neon-glow)" : ""}
                    style={{ transition: 'all 0.3s' }}
                  />

                  {/* Hierarchical Label Rendering */}
                  {showLabel && (
                    <g transform={`translate(0, ${isCore ? 50 : 30})`}>
                      <text 
                        textAnchor="middle" 
                        fill={isCore ? 'var(--primary)' : (isPilar ? '#f59e0b' : '#fff')} 
                        fontSize={isCore ? "16" : (isPilar ? "12" : "10")} 
                        style={{ 
                          fontWeight: isCore ? 900 : 700, 
                          pointerEvents: 'none',
                          textShadow: '0 0 10px rgba(0,0,0,0.9)',
                          letterSpacing: isCore ? '2px' : '1px'
                        }}
                      >
                        {node.id.toUpperCase()}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
          
          {/* Detail Overlay */}
          {selectedNode && (
            <div className="glass-card" style={{ position: 'absolute', bottom: '30px', left: '30px', width: '380px', zIndex: 20, background: 'rgba(5, 8, 18, 0.98)', border: '1px solid var(--primary)', padding: '30px', boxShadow: '0 0 50px rgba(0,242,255,0.2)', animation: 'slideUp 0.3s' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--primary)', fontWeight: 'bold', letterSpacing: '3px' }}>NEURAL_NODE_DATA</span>
                <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '1.5rem' }}>&times;</button>
              </div>
              <h3 style={{ color: 'white', fontSize: '1.6rem', marginBottom: '15px' }}>{selectedNode.id}</h3>
              <div style={{ background: 'rgba(255,255,255,0.04)', padding: '20px', borderRadius: '15px', marginBottom: '25px', borderLeft: '4px solid var(--primary)' }}>
                <p style={{ color: '#eee', fontSize: '0.9rem', lineHeight: '1.7' }}>
                  {selectedNode.type === 'core' ? 'Primary Nexus. Managing all cognitive orchestration and decentralized agent coordination.' : 
                   selectedNode.type === 'pilar' ? 'Thematic Cluster. Higher order organization of related technical concepts and logic vectors.' : 
                   'Knowledge Concept. Atomic intelligence unit validated through recursive system interactions.'}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '15px' }}>
                <span className="badge" style={{ background: 'rgba(0,255,128,0.1)', color: '#00ff80', border: '1px solid rgba(0,255,128,0.3)', padding: '5px 15px' }}>HEALTH: ACTIVE</span>
                <span className="badge" style={{ background: 'rgba(0,242,255,0.1)', color: 'var(--primary)', border: '1px solid rgba(0,242,255,0.3)', padding: '5px 15px' }}>TYPE: {selectedNode.type.toUpperCase()}</span>
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
                    const token = "flosetoken_secure_v2";
                    const res = await fetch(`/api/tasks/execute?task_id=PIPELINE&agent_name=${step.agent_name}&token=${token}`, { 
                      method: 'POST' 
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
                  
                  <NapkinVisual visualId={tpl.napkin_visual_id} />

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
        localStorage.setItem('flose_auth', 'true');
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
    localStorage.removeItem('flose_auth');
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
          {['Dashboard', 'Cognitive Map', 'Task Manager', 'Agent Library', 'Pipeline', 'Marketplace', 'FinOps Guardian', 'Settings'].map(tab => (
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
      </main>
    </div>
  );
}

export default App;
