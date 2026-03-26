import React from 'react';
import { useDashboard } from '../api/hooks/useDashboard';
import ActivityFeed from '../components/ActivityFeed';

const KpiCard = ({ label, value, trend, icon, color = 'indigo' }) => {
  return (
    <div className={`p-6 bg-slate-950 border border-slate-800 rounded-2xl relative overflow-hidden group hover:border-${color}-500/30 transition-all shadow-lg`}>
      <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:scale-125 transition-transform`}>
        <span className="text-4xl">{icon}</span>
      </div>
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-8 h-8 rounded-full bg-${color}-500/20 text-${color}-400 flex items-center justify-center text-xs`}>
          {icon}
        </div>
        <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest">{label}</p>
      </div>
      <div className="flex items-end gap-3">
        <h2 className="text-3xl font-black text-slate-100 italic tracking-tighter">{value}</h2>
        <div className="mb-1 text-[10px] font-bold text-emerald-400">
          {trend}
        </div>
      </div>
      <div className={`mt-4 w-full h-1 bg-slate-900 rounded-full overflow-hidden`}>
        <div className={`h-full bg-${color}-500 w-2/3 opacity-50`} />
      </div>
    </div>
  );
};

const DashboardPage = () => {
  const { data, isLoading } = useDashboard();

  if (isLoading) return <div className="p-10 animate-pulse text-indigo-400">⚡ Sincronizando com o BFF...</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            CENTRAL DE COMANDO
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Status da Operação v3.0 // {data?.project_id}</p>
        </div>
        <div className="flex gap-4 relative z-10">
          <div className="px-6 py-2 bg-indigo-600/10 border border-indigo-500/20 rounded-full text-xs font-bold text-indigo-400">
            📡 SSE: ATIVO
          </div>
          <div className="px-6 py-2 bg-slate-900 border border-slate-800 rounded-full text-xs font-bold text-slate-400">
            {new Date().toLocaleDateString('pt-BR')}
          </div>
        </div>
        {/* Glow Effects */}
        <div className="absolute top-[-50%] left-[-20%] w-[60%] h-[200%] bg-indigo-600/5 blur-[80px] rounded-full rotate-45" />
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard 
          label="Consumo Hoje" 
          value={`${data?.tokens_today || 0}k`} 
          trend="▲ +12%" 
          icon="⚡" 
          color="indigo" 
        />
        <KpiCard 
          label="Custo Operacional" 
          value={`$${data?.cost_today_usd?.toFixed(4) || '0.00'}`} 
          trend="▼ -5%" 
          icon="💎" 
          color="purple" 
        />
        <KpiCard 
          label="Chamadas API" 
          value={data?.api_calls || 0} 
          trend="▲ +2%" 
          icon="🔌" 
          color="blue" 
        />
        <KpiCard 
          label="Health Score" 
          value="98.4%" 
          trend="● ESTÁVEL" 
          icon="🩺" 
          color="emerald" 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="p-8 bg-slate-950 border border-slate-800 rounded-3xl shadow-2xl relative">
            <h3 className="text-lg font-black italic tracking-tighter mb-6">MÉTRICAS DE PERFORMANCE</h3>
            <div className="h-64 flex items-end justify-between gap-2 px-4 border-b border-slate-900">
              {[60, 80, 45, 90, 100, 75, 85].map((h, i) => (
                <div key={i} className="flex-1 group relative">
                  <div 
                    className="bg-indigo-600/20 group-hover:bg-indigo-600/40 border border-indigo-500/20 rounded-t-lg transition-all" 
                    style={{ height: `${h}%` }}
                  >
                    <div className="absolute top-[-25px] left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 bg-slate-900 text-[8px] font-bold p-1 rounded transition-opacity">
                      {h}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-4 px-2">
              {['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM'].map(d => (
                <span key={d} className="text-[9px] text-slate-600 font-bold tracking-widest uppercase">{d}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="p-6 bg-slate-950 border border-slate-800 rounded-3xl shadow-2xl">
            <h3 className="text-sm font-black italic tracking-tighter mb-6 uppercase">ATIVIDADE RECENTE (v3 SSE)</h3>
            <ActivityFeed />
            <button className="w-full mt-6 py-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-indigo-400 transition-all">
              Ver Log Completo 📋
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
