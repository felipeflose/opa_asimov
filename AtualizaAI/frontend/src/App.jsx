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

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
      const interval = setInterval(fetchData, 30000); 
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  // Hook de Física Simplificado (Inspirado no Ref)
  const useForce = (nodes, links, width, height) => {
    const [positions, setPositions] = useState({});
    const simulationRef = useRef(null);

    useEffect(() => {
      if (!nodes.length) return;
      
      const pos = {};
      const vel = {};
      const cx = width / 2;
      const cy = height / 2;

      nodes.forEach((n, i) => {
        const angle = (i / nodes.length) * Math.PI * 2;
        const dist = n.type === 'core' ? 0 : (n.type === 'pilar' ? 120 : 220);
        pos[n.id] = { x: cx + Math.cos(angle) * dist + (Math.random()-0.5)*50, y: cy + Math.sin(angle) * dist + (Math.random()-0.5)*50 };
        vel[n.id] = { x: 0, y: 0 };
      });

      let iteration = 0;
      const step = () => {
        iteration++;
        const alpha = Math.max(0.01, 0.4 * Math.exp(-iteration * 0.015));
        
        // Repulsão
        nodes.forEach(n1 => {
          nodes.forEach(n2 => {
            if (n1.id === n2.id) return;
            const dx = pos[n2.id].x - pos[n1.id].x;
            const dy = pos[n2.id].y - pos[n1.id].y;
            const d = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (2500 / (d * d)) * alpha;
            vel[n1.id].x -= (dx / d) * force;
            vel[n1.id].y -= (dy / d) * force;
          });
        });

        // Atração (Links)
        links.forEach(l => {
          const s = pos[l.source];
          const t = pos[l.target];
          if (!s || !t) return;
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const d = Math.sqrt(dx * dx + dy * dy) || 1;
          const ideal = l.type === 'concept_link' ? 80 : 150;
          const force = (d - ideal) * 0.06 * alpha;
          vel[l.source].x += (dx / d) * force;
          vel[l.source].y += (dy / d) * force;
          vel[l.target].x -= (dx / d) * force;
          vel[l.target].y -= (dy / d) * force;
        });

        // Gravidade Central
        nodes.forEach(n => {
          vel[n.id].x += (cx - pos[n.id].x) * 0.005 * alpha;
          vel[n.id].y += (cy - pos[n.id].y) * 0.005 * alpha;
          
          pos[n.id].x += vel[n.id].x;
          pos[n.id].y += vel[n.id].y;
          
          vel[n.id].x *= 0.85;
          vel[n.id].y *= 0.85;
          
          pos[n.id].x = Math.max(50, Math.min(width - 50, pos[n.id].x));
          pos[n.id].y = Math.max(50, Math.min(height - 50, pos[n.id].y));
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
    const pos = useForce(data.nodes || [], data.links || [], 1000, 600);
    
    return (
      <div className="glass-card graph-container" style={{ height: '70vh', position: 'relative', overflow: 'hidden' }}>
        <h2 className="title-grad" style={{ letterSpacing: '2px', fontSize: '1.2rem' }}>KNOWLEDGE_GRAPH_V3.0</h2>
        <div style={{ height: '100%', width: '100%', position: 'relative' }}>
          <svg width="100%" height="100%" viewBox="0 0 1000 600">
            <defs>
              <filter id="glow-node">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
            </defs>

            {/* Pillar Halos */}
            {data.nodes.filter(n => n.type === 'pilar').map(pilar => {
              const p = pos[pilar.id];
              if (!p) return null;
              return (
                <circle key={`halo-${pilar.id}`} cx={p.x} cy={p.y} r="70" fill="var(--primary)" fillOpacity="0.04" stroke="var(--primary)" strokeOpacity="0.15" strokeDasharray="5 5" className="graph-halo" />
              );
            })}

            {/* Links */}
            {data.links.map((link, i) => {
              const s = pos[link.source];
              const t = pos[link.target];
              if (!s || !t) return null;
              const isHigh = hoveredNode && (hoveredNode.id === link.source || hoveredNode.id === link.target);
              return (
                <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke={isHigh ? 'var(--primary)' : 'var(--primary)'} strokeOpacity={isHigh ? 0.6 : 0.08} strokeWidth={isHigh ? 2 : 1} style={{ transition: 'stroke-opacity 0.3s' }} />
              );
            })}

            {/* Nodes */}
            {data.nodes.map(node => {
              const p = pos[node.id];
              if (!p) return null;
              const isCore = node.type === 'core';
              const isPilar = node.type === 'pilar';
              const isSel = selectedNode && selectedNode.id === node.id;
              const isHov = hoveredNode && hoveredNode.id === node.id;
              
              return (
                <g key={node.id} transform={`translate(${p.x}, ${p.y})`} className="graph-node" onMouseEnter={() => setHoveredNode(node)} onMouseLeave={() => setHoveredNode(null)} onClick={(e) => { e.stopPropagation(); setSelectedNode(node); }}>
                  {(isSel || isHov) && <circle r={isCore ? 35 : (isPilar ? 20 : 12)} fill="var(--primary)" fillOpacity="0.1" filter="url(#glow-node)" />}
                  <circle r={isCore ? 25 : (isPilar ? 12 : 6)} fill={isCore ? 'var(--primary)' : (isPilar ? '#f59e0b' : '#34d399')} stroke={isSel ? 'white' : 'none'} strokeWidth="2" filter={isCore ? "url(#glow-node)" : ""} />
                  <text dy={isCore ? 45 : 22} textAnchor="middle" fill="white" fontSize={isCore ? "14" : "10"} className="graph-label" style={{ fontWeight: (isSel || isHov) ? 700 : 400, opacity: (hoveredNode && !isHov) ? 0.3 : 0.8 }}>
                    {node.id.toUpperCase()}
                  </text>
                </g>
              );
            })}
          </svg>
          
          {/* Side Info overlay */}
          {selectedNode && (
            <div className="glass-card" style={{ position: 'absolute', top: '20px', right: '20px', width: '280px', zIndex: 10, background: 'rgba(5,8,16,0.95)', border: '1px solid var(--primary)', fontFamily: 'inherit' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--primary)', fontWeight: 'bold', letterSpacing: '1px' }}>DATA_ENTRY // {selectedNode.type.toUpperCase()}</span>
                <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontSize: '1.2rem' }}>&times;</button>
              </div>
              <h3 style={{ color: 'white', fontSize: '1.2rem' }}>{selectedNode.id}</h3>
              <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid var(--primary)' }}>
                <p style={{ fontSize: '0.8rem', color: '#e0e0e0', lineHeight: '1.5' }}>
                  {selectedNode.type === 'core' ? 'Núcleo Central da Plataforma. Representa a Flose AI e o orquestrador cognitivo.' : 
                   selectedNode.type === 'pilar' ? 'Pilar Tecnológico. Agrupa conceitos correlacionados identificados pelo sistema.' : 
                   'Conceito Específico. Item de conhecimento granular capturado durante execuções autônomas.'}
                </p>
              </div>
              <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '5px', textAlign: 'center' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 'bold', color: 'var(--primary)' }}>1</div>
                  <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>LEVEL</div>
                </div>
                <div style={{ flex: 1, background: 'rgba(0,0,0,0.5)', padding: '10px', borderRadius: '5px', textAlign: 'center' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#f59e0b' }}>A+</div>
                  <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>RELATION</div>
                </div>
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
            <div className="glass-card" style={{ height: '400px', position: 'relative' }}>
              <h4 style={{ marginBottom: '20px' }}>Quick Insight: Cognitive Map</h4>
              <div style={{ height: '80%', overflow: 'hidden' }}>
                <svg width="100%" height="100%" viewBox="0 0 800 400">
                  {graphData.links && graphData.links.map((link, i) => {
                    const source = graphData.nodes.find(n => n.id === link.source);
                    const target = graphData.nodes.find(n => n.id === link.target);
                    if (!source || !target) return null;
                    return <line key={i} x1={400 + (Math.random()*100)} y1={200 + (Math.random()*100)} x2={400} y2={200} stroke="rgba(255,255,255,0.1)" />
                  })}
                  {graphData.nodes && graphData.nodes.slice(0, 15).map((node, i) => (
                    <g key={node.id} transform={`translate(${400 + Math.cos(i)*150}, ${200 + Math.sin(i)*120})`}>
                      <circle r="6" fill={node.type === 'core' ? 'var(--primary)' : 'var(--secondary)'} />
                      <text dy="15" textAnchor="middle" fill="white" fontSize="8">{node.id}</text>
                    </g>
                  ))}
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
          {['Dashboard', 'Cognitive Map', 'Task Manager', 'Agent Library', 'FinOps Guardian', 'Settings'].map(tab => (
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
