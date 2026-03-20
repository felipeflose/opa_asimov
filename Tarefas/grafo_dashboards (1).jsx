import { useState, useEffect, useRef, useCallback } from "react";

const GRAPH_DATA = {
  nodes: [
    { id:"Painel Juridico", origem:"Jurídico", identificador:"R003", status:"Pendente", totalPkgs:1, prioridade:"1", classifCarga:"M" },
    { id:"junto com Movimentação de Carga", origem:"Operação", identificador:"R004", status:"Carga Inicial", totalPkgs:1, prioridade:"1", classifCarga:"G" },
    { id:"Receita Atual", origem:"Gestão Executiva", identificador:"R006", status:"Pendente", totalPkgs:0, prioridade:"2", classifCarga:"P" },
    { id:"Coleta Eficacia", origem:"Operação", identificador:"R007", status:"finalizado", totalPkgs:8, prioridade:"2", classifCarga:"G" },
    { id:"MAPA_VENDAS", origem:"BI Legado - Controladoria", identificador:"R008", status:"Pendente", totalPkgs:0, prioridade:"3", classifCarga:"G" },
    { id:"Entrega Filial", origem:"Operação", identificador:"R009", status:"em andamento", totalPkgs:6, prioridade:"3", classifCarga:"G" },
    { id:"ACOMPANHAMENTO_COMBUSTIVEL", origem:"BI Legado - Controladoria", identificador:"R010", status:"Pendente", totalPkgs:0, prioridade:"4", classifCarga:"M" },
    { id:"Transferência", origem:"Operação", identificador:"R011", status:"Pendente", totalPkgs:1, prioridade:"4", classifCarga:"G" },
    { id:"Painel DRE", origem:"Controladoria", identificador:"R012", status:"Pendente", totalPkgs:0, prioridade:"5", classifCarga:"G" },
    { id:"Gestao de Ocorrencia", origem:"Operação", identificador:"R013", status:"Pendente", totalPkgs:24, prioridade:"5", classifCarga:"G" },
    { id:"Gestao de Indenizacao", origem:"Operação", identificador:"R014", status:"Pendente", totalPkgs:4, prioridade:"6", classifCarga:"G" },
    { id:"INADIMPLENCIA", origem:"BI Legado - Controladoria", identificador:"R015", status:"Pendente", totalPkgs:0, prioridade:"7", classifCarga:"M" },
    { id:"DRE Indenização", origem:"Operação", identificador:"R016", status:"Pendente", totalPkgs:2, prioridade:"7", classifCarga:"M" },
    { id:"DESCONTOS_CONCEDIDOS", origem:"BI Legado - Controladoria", identificador:"R017", status:"Pendente", totalPkgs:0, prioridade:"8", classifCarga:"M" },
    { id:"Faturamento - Realizado X Orçado", origem:"Operação", identificador:"R018", status:"Pendente", totalPkgs:2, prioridade:"9", classifCarga:"G" },
    { id:"Comprovação de Entrega", origem:"Operação", identificador:"R019", status:"Pendente", totalPkgs:5, prioridade:"10", classifCarga:"M" },
    { id:"Painel de Entrega", origem:"Operação", identificador:"R020", status:"Pendente", totalPkgs:33, prioridade:"11", classifCarga:"G" },
    { id:"Produtividade de Veículo", origem:"Operação", identificador:"R021", status:"Pendente", totalPkgs:19, prioridade:"12", classifCarga:"G" },
    { id:"Comissão do Agente", origem:"Operação", identificador:"R022", status:"Pendente", totalPkgs:5, prioridade:"13", classifCarga:"G" },
    { id:"Painel PCP - Viagem de Transferência", origem:"Operação", identificador:"R023", status:"Pendente", totalPkgs:3, prioridade:"14", classifCarga:"M" },
    { id:"Valor de Carga Armazém", origem:"Operação", identificador:"R024", status:"Pendente", totalPkgs:5, prioridade:"15", classifCarga:"M" },
    { id:"Viagens de Transferência", origem:"Operação", identificador:"R025", status:"Pendente", totalPkgs:7, prioridade:"16", classifCarga:"G" },
    { id:"Análise de Volumetria", origem:"Operação", identificador:"R026", status:"Pendente", totalPkgs:3, prioridade:"17", classifCarga:"M" },
    { id:"Painel de Coletas", origem:"Operação", identificador:"R027", status:"Pendente", totalPkgs:6, prioridade:"18", classifCarga:"G" },
    { id:"Gestao de Sinistros", origem:"Operação", identificador:"R028", status:"Pendente", totalPkgs:4, prioridade:"19", classifCarga:"M" },
    { id:"PROJECAO_RECEBIMENTOS", origem:"BI Legado - Contas a Pagar", identificador:"R030", status:"Pendente", totalPkgs:0, prioridade:"20", classifCarga:"M" },
    { id:"BANCO_HORAS", origem:"BI Legado - RH", identificador:"R031", status:"Pendente", totalPkgs:0, prioridade:"21", classifCarga:"P" },
    { id:"Posição de Fornecedores", origem:"Controladoria", identificador:"R037", status:"Pendente", totalPkgs:0, prioridade:"22", classifCarga:"M" },
    { id:"Avaliação Operacional (Ranking)", origem:"Operação", identificador:"R038", status:"Pendente", totalPkgs:1, prioridade:"23", classifCarga:"M" },
    { id:"Relatório - Fechamento Forçado", origem:"Operação", identificador:"R039", status:"Pendente", totalPkgs:8, prioridade:"24", classifCarga:"M" },
    { id:"Relatório Reimpressão Etiquetas", origem:"Operação", identificador:"R040", status:"nan", totalPkgs:6, prioridade:"25", classifCarga:"P" },
    { id:"Gestão de Reentrega", origem:"Operação", identificador:"R041", status:"nan", totalPkgs:3, prioridade:"26", classifCarga:"M" },
    { id:"Painel CCO", origem:"Operação", identificador:"R042", status:"Pendente", totalPkgs:1, prioridade:"27", classifCarga:"G" },
    { id:"Documento de Transporte", origem:"Operação", identificador:"R043", status:"Pendente", totalPkgs:0, prioridade:"28", classifCarga:"M" },
    { id:"Sem Viagem", origem:"Operação", identificador:"R044", status:"Pendente", totalPkgs:1, prioridade:"29", classifCarga:"P" },
    { id:"Gestão de Transporte", origem:"Operação", identificador:"R045", status:"Pendente", totalPkgs:0, prioridade:"30", classifCarga:"M" },
    { id:"Painel Gestão de Frota", origem:"Operação", identificador:"R046", status:"Pendente", totalPkgs:4, prioridade:"31", classifCarga:"G" },
    { id:"Peso Cubagem", origem:"Operação", identificador:"R047", status:"Pendente", totalPkgs:4, prioridade:"32", classifCarga:"M" },
  ],
  edges: [
    { source:"Coleta Eficacia", target:"Entrega Filial", sharedPkgs:["PKG_DIM_OCORRENCIA_TRANSPORTE","PKG_DIM_FILIAL","PKG_DIM_CIDADE_PROTHEUS","PKG_DIM_ROTA"], count:4 },
    { source:"Coleta Eficacia", target:"Gestao de Indenizacao", sharedPkgs:["PKG_DIM_OCORRENCIA_TRANSPORTE"], count:1 },
    { source:"Entrega Filial", target:"Gestao de Indenizacao", sharedPkgs:["PKG_DIM_OCORRENCIA_TRANSPORTE"], count:1 },
    { source:"Gestao de Ocorrencia", target:"Relatório Reimpressão Etiquetas", sharedPkgs:["PCT_001_STAGE_INDENIZACAO","PCT_002_FATO_INDENIZACAO","PCT_003_EXC_SSAS_INDENIZACAO","PCT_SEQ_INDENIZACAO"], count:4 },
    { source:"Gestao de Ocorrencia", target:"Gestao de Indenizacao", sharedPkgs:["PKG_DIM_DOC_CLIENTE_TRANSPORTE"], count:1 },
    { source:"Gestao de Ocorrencia", target:"Painel de Entrega", sharedPkgs:["PCT_011_FAT_IND_PND"], count:1 },
    { source:"Painel de Entrega", target:"Relatório - Fechamento Forçado", sharedPkgs:["PCT_002_STAGE_PCP2_V2","PCT_008_FATO_PCP2","SSAS_PCP2"], count:3 },
    { source:"Painel de Entrega", target:"Gestao de Indenizacao", sharedPkgs:["PKG_DIM_OCORRENCIA_CONHECIMENTO_V3"], count:1 },
    { source:"Viagens de Transferência", target:"Relatório - Fechamento Forçado", sharedPkgs:["PCT_002_FAT_OCO_OPE"], count:1 },
    { source:"DRE Indenização", target:"Faturamento - Realizado X Orçado", sharedPkgs:["*USA O MAPA_VENDAS","SERÁ TRATADO POSTERIORMENTE*"], count:2 },
    { source:"Avaliação Operacional (Ranking)", target:"Painel CCO", sharedPkgs:["Todos já mapeados em outros projetos"], count:1 },
    { source:"Avaliação Operacional (Ranking)", target:"Sem Viagem", sharedPkgs:["Todos já mapeados em outros projetos"], count:1 },
    { source:"Painel CCO", target:"Sem Viagem", sharedPkgs:["Todos já mapeados em outros projetos"], count:1 },
  ]
};

const ORIGEM_COLORS = {
  "Operação":                  "#3b82f6",
  "BI Legado - Controladoria": "#a855f7",
  "BI Legado - Contas a Pagar":"#f97316",
  "BI Legado - RH":            "#ec4899",
  "Controladoria":             "#14b8a6",
  "Gestão Executiva":          "#eab308",
  "Jurídico":                  "#ef4444",
};

const STATUS_META = {
  "finalizado":    { ring:"#22c55e", label:"Finalizado" },
  "em andamento":  { ring:"#f59e0b", label:"Em Andamento" },
  "Carga Inicial": { ring:"#818cf8", label:"Carga Inicial" },
  "Pendente":      { ring:null,      label:"Pendente" },
  "nan":           { ring:"#475569", label:"Sem Status" },
};

function useForce(nodes, edges, w, h) {
  const pos = useRef({});
  const vel = useRef({});
  const iter = useRef(0);
  const raf = useRef(null);
  const [, tick] = useState(0);

  useEffect(() => {
    if (!w || !h || !nodes.length) return;
    const cx = w / 2, cy = h / 2;
    const origens = [...new Set(nodes.map(n => n.origem))];
    const clusterR = Math.min(w, h) * 0.32;

    nodes.forEach(n => {
      if (pos.current[n.id]) return;
      const oi = origens.indexOf(n.origem);
      const angle = (2 * Math.PI * oi) / origens.length;
      pos.current[n.id] = { x: cx + clusterR * Math.cos(angle) + (Math.random()-.5)*60, y: cy + clusterR * Math.sin(angle) + (Math.random()-.5)*60 };
      vel.current[n.id] = { x:0, y:0 };
    });
    iter.current = 0;

    const clusterCenters = {};
    origens.forEach((o, oi) => {
      const angle = (2 * Math.PI * oi) / origens.length;
      clusterCenters[o] = { x: cx + clusterR * Math.cos(angle), y: cy + clusterR * Math.sin(angle) };
    });

    const step = () => {
      iter.current++;
      const a = Math.max(0.005, 0.65 * Math.exp(-iter.current * 0.014));
      const p = pos.current, v = vel.current;
      const ids = nodes.map(n => n.id);

      for (let i = 0; i < ids.length; i++)
        for (let j = i+1; j < ids.length; j++) {
          const A = ids[i], B = ids[j];
          const dx = p[B].x-p[A].x, dy = p[B].y-p[A].y;
          const d = Math.sqrt(dx*dx+dy*dy)||1;
          const f = (3200/(d*d))*a;
          v[A].x -= dx/d*f; v[A].y -= dy/d*f;
          v[B].x += dx/d*f; v[B].y += dy/d*f;
        }

      edges.forEach(e => {
        if (!p[e.source]||!p[e.target]) return;
        const dx = p[e.target].x-p[e.source].x, dy = p[e.target].y-p[e.source].y;
        const d = Math.sqrt(dx*dx+dy*dy)||1;
        const ideal = 130+e.count*14;
        const f = ((d-ideal)/d)*0.075*a;
        v[e.source].x+=dx*f; v[e.source].y+=dy*f;
        v[e.target].x-=dx*f; v[e.target].y-=dy*f;
      });

      nodes.forEach(n => {
        const cc = clusterCenters[n.origem];
        if (!cc) return;
        v[n.id].x += (cc.x-p[n.id].x)*0.028*a;
        v[n.id].y += (cc.y-p[n.id].y)*0.028*a;
      });

      ids.forEach(id => {
        v[id].x*=0.73; v[id].y*=0.73;
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
}

export default function App() {
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ w:900, h:640 });
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [filterOrigem, setFilterOrigem] = useState("all");
  const [colorBy, setColorBy] = useState("origem");
  const [dragging, setDragging] = useState(null);
  const dragOff = useRef({ x:0, y:0 });
  const posOverride = useRef({});
  const [, forceRender] = useState(0);

  useEffect(() => {
    const obs = new ResizeObserver(e => {
      const { width, height } = e[0].contentRect;
      setDims({ w: Math.max(600,width), h: Math.max(460,height) });
    });
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  const visNodes = filterOrigem === "all" ? GRAPH_DATA.nodes : GRAPH_DATA.nodes.filter(n => n.origem === filterOrigem);
  const visIds = new Set(visNodes.map(n => n.id));
  const visEdges = GRAPH_DATA.edges.filter(e => visIds.has(e.source) && visIds.has(e.target));

  const simPos = useForce(visNodes, visEdges, dims.w, dims.h);
  const getP = id => posOverride.current[id] || simPos[id] || { x:dims.w/2, y:dims.h/2 };

  const active = selected || hovered;
  const activeEdges = active ? visEdges.filter(e => e.source===active||e.target===active) : [];
  const activeIds = new Set(activeEdges.flatMap(e=>[e.source,e.target]));

  const nodeColor = n => colorBy === "origem"
    ? (ORIGEM_COLORS[n.origem]||"#64748b")
    : ({ finalizado:"#22c55e","em andamento":"#f59e0b","Carga Inicial":"#818cf8",Pendente:"#3b82f6",nan:"#475569" }[n.status]||"#475569");

  const nodeR = n => Math.max(13, Math.min(13+n.totalPkgs*0.72, 30));

  const onMD = useCallback((e, id) => {
    e.stopPropagation();
    const p = getP(id), svg = e.currentTarget.closest("svg"), r = svg.getBoundingClientRect();
    dragOff.current = { x: e.clientX-r.left-p.x, y: e.clientY-r.top-p.y };
    setDragging(id); setSelected(id);
  }, [simPos]);

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
      forceRender(v=>v+1);
    };
    const up = () => setDragging(null);
    window.addEventListener("mousemove", mv); window.addEventListener("mouseup", up);
    return () => { window.removeEventListener("mousemove", mv); window.removeEventListener("mouseup", up); };
  }, [dragging, dims]);

  const selNode = selected ? GRAPH_DATA.nodes.find(n => n.id===selected) : null;
  const selEdges = selected ? visEdges.filter(e => e.source===selected||e.target===selected) : [];
  const origens = Object.keys(ORIGEM_COLORS);

  return (
    <div style={{ width:"100%", height:"100vh", background:"#050810", display:"flex", flexDirection:"column", fontFamily:"'JetBrains Mono','Fira Code',monospace", overflow:"hidden" }}>

      {/* Header */}
      <div style={{ padding:"9px 16px", borderBottom:"1px solid #0d1117", background:"#050810", flexShrink:0, display:"flex", gap:10, flexWrap:"wrap", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <span style={{ color:"#60a5fa", fontSize:11, fontWeight:700, letterSpacing:3 }}>GCP MIGRATION · DEPENDENCY GRAPH</span>
          <span style={{ color:"#1e293b", fontSize:9, marginLeft:10 }}>{visNodes.length} dashboards · {visEdges.length} conexões SSIS</span>
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center", flexWrap:"wrap" }}>
          {/* color mode */}
          <div style={{ display:"flex", borderRadius:4, overflow:"hidden", border:"1px solid #0d1117" }}>
            {["origem","status"].map(m => (
              <button key={m} onClick={()=>setColorBy(m)} style={{
                padding:"3px 9px", fontSize:8, cursor:"pointer", border:"none", fontFamily:"inherit",
                background: colorBy===m ? "#1d4ed8":"transparent",
                color: colorBy===m ? "#fff":"#334155",
                fontWeight: colorBy===m ? 700:400,
              }}>COR/{m.toUpperCase()}</button>
            ))}
          </div>
          {/* origem filters */}
          <button onClick={()=>setFilterOrigem("all")} style={{ padding:"3px 8px", fontSize:8, borderRadius:3, cursor:"pointer", fontFamily:"inherit", background:filterOrigem==="all"?"#1e293b":"transparent", border:`1px solid ${filterOrigem==="all"?"#3b82f6":"#0d1117"}`, color:filterOrigem==="all"?"#60a5fa":"#334155" }}>TODOS</button>
          {origens.map(o => {
            const c = ORIGEM_COLORS[o], act = filterOrigem===o;
            return <button key={o} onClick={()=>setFilterOrigem(act?"all":o)} style={{ padding:"3px 8px", fontSize:8, borderRadius:3, cursor:"pointer", fontFamily:"inherit", background:act?c+"22":"transparent", border:`1px solid ${act?c:"#0d1117"}`, color:act?c:"#334155", fontWeight:act?700:400 }}>{o.replace("BI Legado - ","BIL·").toUpperCase()}</button>;
          })}
        </div>
      </div>

      <div style={{ flex:1, display:"flex", overflow:"hidden" }}>

        {/* Graph canvas */}
        <div ref={containerRef} style={{ flex:1, position:"relative", overflow:"hidden" }} onClick={()=>setSelected(null)}>
          <svg width={dims.w} height={dims.h} style={{ display:"block" }}>
            <defs>
              <filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
              <filter id="sg"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
            </defs>

            {/* Cluster halos */}
            {colorBy === "origem" && (() => {
              const groups = {};
              visNodes.forEach(n => { if (!groups[n.origem]) groups[n.origem]=[]; groups[n.origem].push(n.id); });
              return Object.entries(groups).map(([o,ids]) => {
                const pts = ids.map(id=>getP(id)).filter(Boolean);
                if (!pts.length) return null;
                const mx = pts.reduce((s,p)=>s+p.x,0)/pts.length;
                const my = pts.reduce((s,p)=>s+p.y,0)/pts.length;
                const rr = Math.max(45, Math.max(...pts.map(p=>Math.hypot(p.x-mx,p.y-my)))+32);
                const c = ORIGEM_COLORS[o]||"#64748b";
                return <circle key={o} cx={mx} cy={my} r={rr} fill={c+"07"} stroke={c+"1a"} strokeWidth={1} style={{ pointerEvents:"none" }}/>;
              });
            })()}

            {/* Edges */}
            {visEdges.map((e,i) => {
              const sp=getP(e.source), tp=getP(e.target);
              if (!sp||!tp) return null;
              const isAct = activeEdges.includes(e);
              const mx=(sp.x+tp.x)/2, my=(sp.y+tp.y)/2;
              return (
                <g key={i}>
                  <line x1={sp.x} y1={sp.y} x2={tp.x} y2={tp.y}
                    stroke={isAct?"#60a5fa":"#0f172a"}
                    strokeWidth={isAct ? Math.min(2+e.count,6) : Math.min(1+e.count*.8,4.5)}
                    strokeOpacity={isAct ? 1 : (active ? 0.07 : 0.55)}
                    style={{ transition:"stroke 0.18s, stroke-opacity 0.18s" }}/>
                  {isAct && <text x={mx} y={my-7} textAnchor="middle" fontSize={8} fill="#60a5fa" style={{ pointerEvents:"none" }}>{e.count} pkg{e.count>1?"s":""}</text>}
                </g>
              );
            })}

            {/* Nodes */}
            {visNodes.map(n => {
              const p = getP(n.id); if (!p) return null;
              const col = nodeColor(n), r = nodeR(n);
              const isSel=selected===n.id, isHov=hovered===n.id;
              const isDim = active && !activeIds.has(n.id) && active!==n.id;
              const sm = STATUS_META[n.status]||STATUS_META["nan"];
              return (
                <g key={n.id} transform={`translate(${p.x},${p.y})`} style={{ cursor:"grab" }}
                  onMouseDown={ev=>onMD(ev,n.id)}
                  onClick={ev=>{ ev.stopPropagation(); setSelected(isSel?null:n.id); }}
                  onMouseEnter={()=>setHovered(n.id)} onMouseLeave={()=>setHovered(null)}>

                  {sm.ring && <circle r={r+5} fill="none" stroke={sm.ring} strokeWidth={1.5} strokeDasharray={n.status==="em andamento"?"4 3":"none"} strokeOpacity={isDim?.05:.55} style={{ pointerEvents:"none" }}/>}
                  {(isSel||isHov) && <circle r={r+5} fill={col} fillOpacity={.12} style={{ filter:"url(#glow)", pointerEvents:"none" }}/>}

                  <circle r={r} fill={col} fillOpacity={isDim?.07:.9} stroke={isSel?"#fff":col} strokeWidth={isSel?2:1} strokeOpacity={isDim?.08:.85}
                    style={{ transition:"fill-opacity .18s", filter:isSel?"url(#sg)":"none" }}/>

                  <text textAnchor="middle" dominantBaseline="middle"
                    fontSize={n.totalPkgs>0 ? Math.max(8,Math.min(r*.56,13)) : 11}
                    fill="#fff" fontWeight="700" fillOpacity={isDim?.08:1} style={{ pointerEvents:"none", userSelect:"none" }}>
                    {n.totalPkgs>0 ? n.totalPkgs : "·"}
                  </text>
                  <text y={r+11} textAnchor="middle" fontSize={9} fill={isDim?"#0d1117":"#94a3b8"}
                    fontWeight={isSel?700:400} style={{ pointerEvents:"none", userSelect:"none", transition:"fill .18s" }}>
                    {n.id.length>21 ? n.id.slice(0,19)+"…" : n.id}
                  </text>
                  {!isDim && n.identificador && (
                    <text y={-r-5} textAnchor="middle" fontSize={7} fill={col} fillOpacity={.65} style={{ pointerEvents:"none", userSelect:"none" }}>{n.identificador}</text>
                  )}
                </g>
              );
            })}
          </svg>

          {/* Legend */}
          <div style={{ position:"absolute", bottom:10, left:10, background:"rgba(5,8,16,.93)", border:"1px solid #0d1117", borderRadius:6, padding:"8px 11px" }}>
            <div style={{ color:"#1e293b", fontSize:7.5, letterSpacing:2, marginBottom:5 }}>{colorBy==="origem"?"ORIGEM":"STATUS"}</div>
            {colorBy==="origem"
              ? origens.map(o => (
                  <div key={o} style={{ display:"flex", alignItems:"center", gap:5, marginBottom:2 }}>
                    <div style={{ width:7, height:7, borderRadius:"50%", background:ORIGEM_COLORS[o], flexShrink:0 }}/>
                    <span style={{ color:"#334155", fontSize:7.5 }}>{o}</span>
                  </div>
                ))
              : Object.entries(STATUS_META).map(([k,v]) => (
                  <div key={k} style={{ display:"flex", alignItems:"center", gap:5, marginBottom:2 }}>
                    <div style={{ width:7, height:7, borderRadius:"50%", background:v.ring||"#3b82f6", flexShrink:0 }}/>
                    <span style={{ color:"#334155", fontSize:7.5 }}>{v.label}</span>
                  </div>
                ))
            }
            <div style={{ marginTop:6, borderTop:"1px solid #0d1117", paddingTop:5, color:"#1e293b", fontSize:7, lineHeight:1.7 }}>
              Número = PKGs no SSIS<br/>
              Espessura = PKGs em comum<br/>
              Anel = status da carga
            </div>
          </div>
        </div>

        {/* Side panel */}
        <div style={{ width:selNode?285:0, flexShrink:0, background:"#05080e", borderLeft:"1px solid #0d1117", overflow:"hidden", transition:"width .22s ease", display:"flex", flexDirection:"column" }}>
          {selNode && (() => {
            const c = ORIGEM_COLORS[selNode.origem]||"#64748b";
            const sm = STATUS_META[selNode.status]||STATUS_META.nan;
            return (
              <div style={{ padding:15, overflowY:"auto", flex:1 }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:9 }}>
                  <span style={{ color:c, fontSize:8.5, fontWeight:700, letterSpacing:2 }}>{selNode.identificador}</span>
                  <button onClick={()=>setSelected(null)} style={{ background:"none", border:"none", color:"#1e293b", cursor:"pointer", fontSize:14 }}>✕</button>
                </div>

                <div style={{ color:"#e2e8f0", fontSize:13, fontWeight:700, lineHeight:1.4, marginBottom:9 }}>{selNode.id}</div>

                <div style={{ display:"inline-flex", alignItems:"center", gap:5, padding:"3px 8px", borderRadius:3, background:c+"18", border:`1px solid ${c}33`, marginBottom:5 }}>
                  <div style={{ width:6, height:6, borderRadius:"50%", background:c }}/>
                  <span style={{ color:c, fontSize:8.5, fontWeight:700 }}>{selNode.origem}</span>
                </div>

                <div style={{ marginBottom:12 }}>
                  <span style={{ color:"#1e293b", fontSize:7.5, letterSpacing:2 }}>STATUS · </span>
                  <span style={{ color:sm.ring||"#3b82f6", fontSize:8.5, fontWeight:700 }}>{sm.label}</span>
                  {selNode.classifCarga && <>
                    <span style={{ marginLeft:10, color:"#1e293b", fontSize:7.5, letterSpacing:2 }}>CARGA · </span>
                    <span style={{ color:"#60a5fa", fontSize:8.5, fontWeight:700 }}>{selNode.classifCarga}</span>
                  </>}
                </div>

                <div style={{ display:"flex", gap:7, marginBottom:13 }}>
                  {[["PKGs SSIS", selNode.totalPkgs, c],["CONEXÕES", selEdges.length, "#f59e0b"],["PRIORIDADE", selNode.prioridade, "#e2e8f0"]].map(([l,v,vc])=>(
                    <div key={l} style={{ flex:1, background:"#0a0f1a", border:"1px solid #0d1117", borderRadius:5, padding:"7px 5px", textAlign:"center" }}>
                      <div style={{ color:vc, fontSize:19, fontWeight:700 }}>{v}</div>
                      <div style={{ color:"#1e293b", fontSize:7.5 }}>{l}</div>
                    </div>
                  ))}
                </div>

                {selEdges.length > 0 ? (
                  <>
                    <div style={{ color:"#1e293b", fontSize:7.5, letterSpacing:2, marginBottom:6 }}>COMPARTILHA PKGs COM</div>
                    {selEdges.map((e,i) => {
                      const other = e.source===selNode.id ? e.target : e.source;
                      const on = GRAPH_DATA.nodes.find(n=>n.id===other);
                      const oc = on ? (ORIGEM_COLORS[on.origem]||"#64748b") : "#64748b";
                      return (
                        <div key={i} onClick={()=>setSelected(other)} style={{ background:"#0a0f1a", borderRadius:5, padding:"8px 10px", marginBottom:5, border:`1px solid ${oc}28`, cursor:"pointer", transition:"border-color .15s" }}
                          onMouseEnter={ev=>ev.currentTarget.style.borderColor=oc}
                          onMouseLeave={ev=>ev.currentTarget.style.borderColor=oc+"28"}>
                          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:3 }}>
                            <span style={{ color:"#cbd5e1", fontSize:9.5, fontWeight:700, lineHeight:1.3 }}>{other.length>24?other.slice(0,22)+"…":other}</span>
                            <span style={{ color:oc, fontSize:8, marginLeft:4, flexShrink:0, fontWeight:700 }}>{e.count} pkg{e.count>1?"s":""}</span>
                          </div>
                          {on && <div style={{ display:"flex", alignItems:"center", gap:4, marginBottom:4 }}>
                            <div style={{ width:5, height:5, borderRadius:"50%", background:oc }}/>
                            <span style={{ color:"#1e3a5f", fontSize:7.5 }}>{on.origem}</span>
                          </div>}
                          <div>
                            {e.sharedPkgs.slice(0,4).map((p,j)=>(
                              <div key={j} style={{ fontSize:7.5, color:"#334155", lineHeight:1.6 }}>· {p.length>35?p.slice(0,33)+"…":p}</div>
                            ))}
                            {e.sharedPkgs.length>4 && <div style={{ fontSize:7.5, color:"#1e293b" }}>+{e.sharedPkgs.length-4} mais</div>}
                          </div>
                        </div>
                      );
                    })}
                  </>
                ) : (
                  <div style={{ background:"#0a0f1a", borderRadius:5, padding:12, color:"#1e293b", fontSize:9, textAlign:"center", border:"1px solid #0d1117" }}>
                    Nenhum PKG compartilhado<br/>com outros dashboards
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      </div>
    </div>
  );
}
