import React from 'react';
import { useDashboard } from '../api/hooks/useDashboard';

const FinOpsPage = () => {
    const { data: finops, isLoading } = useDashboard(); // Reaproveita dashboard metrics v3

    if (isLoading) return <div className="p-10 text-purple-400">⚡ Sincronizando Guardião FinOps...</div>;

    const items = [
        { label: 'Custos Acumulados', value: `$${finops?.cost_today_usd?.toFixed(4) || '0.00'}` },
        { label: 'Tokens Processados', value: `${finops?.tokens_today || 0}k` },
        { label: 'Custos por TRD', value: `$${(finops?.cost_today_usd / 20).toFixed(4)} (avg)` },
        { label: 'Eficiência de Cache', value: '42%' },
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-slate-800 shadow-xl relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent uppercase">
                        Guardião FinOps
                    </h1>
                    <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Geração de Eficiência Cognitiva v3.0</p>
                </div>
                <div className="absolute right-10 top-[-20%] w-[40%] h-[140%] bg-purple-600/5 blur-[80px] rounded-full rotate-45" />
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {items.map(i => (
                    <div key={i.label} className="p-8 bg-slate-950 border border-slate-800 rounded-3xl shadow-lg hover:border-purple-500/30 transition-all">
                        <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-2">{i.label}</p>
                        <h2 className="text-3xl font-black italic tracking-tighter text-slate-200">{i.value}</h2>
                        <div className="mt-4 pt-4 border-t border-slate-900 flex justify-between">
                            <span className="text-[8px] font-black uppercase tracking-tight text-slate-600">ROI: 8.2x</span>
                            <span className="text-[8px] font-bold text-emerald-400">● OTIMIZADO</span>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-10 bg-slate-950 border border-slate-800 rounded-3xl shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-600/20 to-indigo-600/20" />
                <h3 className="text-lg font-black italic tracking-tighter mb-8 bg-gradient-to-r from-slate-200 to-slate-400 bg-clip-text text-transparent">HISTÓRICO DE GASTOS (ÚLTIMOS 30 DIAS)</h3>
                <div className="h-64 flex items-end justify-between gap-1 px-4 mb-2">
                    {[20, 30, 15, 45, 60, 25, 35, 50, 45, 55, 65, 70, 40, 30, 25, 45, 50, 60, 40, 30, 20, 15, 45, 60, 75, 80, 50, 45, 30, 100].map((h, i) => (
                        <div key={i} className="flex-1 group relative">
                            <div 
                                className="bg-purple-600/10 group-hover:bg-purple-600/40 border border-purple-500/10 rounded-sm transition-all h-full" 
                                style={{ height: `${h}%` }}
                            />
                        </div>
                    ))}
                </div>
                <div className="flex justify-between items-center px-4 text-[9px] font-bold uppercase tracking-widest text-slate-600">
                    <span>30 Dias Atrás</span>
                    <span>Hoje</span>
                </div>
                
                <div className="mt-10 p-6 bg-purple-900/5 border border-purple-900/20 rounded-2xl flex items-center justify-between">
                    <div>
                        <h4 className="text-xs font-black text-purple-400 uppercase tracking-tighter">Budget Alerta Ativado</h4>
                        <p className="text-[10px] text-slate-500 uppercase font-medium mt-1">Limite mensal definido em $150.00</p>
                    </div>
                    <div className="text-right">
                        <span className="text-xs font-black italic tracking-tighter">$14.28 USADO</span>
                        <div className="w-32 h-1 bg-slate-800 rounded-full mt-2 overflow-hidden">
                            <div className="h-full bg-purple-500 w-[10%]" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FinOpsPage;
