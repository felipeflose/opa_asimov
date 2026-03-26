import React, { useState } from 'react';
import { useAgents, useSaveAgent, useDeleteAgent } from '../api/hooks/useAgents';

const AgentsPage = () => {
  const { data: agents, isLoading } = useAgents();
  const saveAgent = useSaveAgent();
  const deleteAgent = useDeleteAgent();
  
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  if (isLoading) return <div className="p-10 text-indigo-400">⚡ Carregando Biblioteca de Agentes...</div>;

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData(e.target);
      const tools = [];
      if (formData.get('tool_google_search')) tools.push('google_search');
      
      const agentData = {
        name: formData.get('name'),
        purpose: formData.get('purpose'),
        system_prompt: formData.get('system_prompt'),
        avatar: selectedAgent?.avatar,
        tools: tools
      };
      
      await saveAgent.mutateAsync(agentData);
      setIsEditing(false);
      setSelectedAgent(null);
    } catch (err) {
      console.error(err);
      alert(`Erro ao salvar agente: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleDelete = async (name) => {
    if (window.confirm(`Tem certeza que deseja deletar o agente '${name}'?`)) {
      await deleteAgent.mutateAsync(name);
      if (selectedAgent?.name === name) setSelectedAgent(null);
    }
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
      <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-purple-400 to-indigo-400 bg-clip-text text-transparent">
            BIBLIOTECA DE AGENTES
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Gestão de Cognição Especializada v3.0</p>
        </div>
        <button 
          onClick={() => { setSelectedAgent({}); setIsEditing(true); }}
          className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-indigo-500/20 shadow-lg active:scale-95"
        >
          Novo Agente +
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Lista de Agentes */}
        <div className="lg:col-span-1 space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
          {agents?.map((agent) => (
            <div 
              key={agent.name}
              onClick={() => { setSelectedAgent(agent); setIsEditing(false); }}
              className={`p-4 bg-slate-950 border rounded-2xl cursor-pointer transition-all group ${selectedAgent?.name === agent.name ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-slate-800 hover:border-slate-700'}`}
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center font-black text-xs shadow-lg">
                  {agent.name.substring(0, 2).toUpperCase()}
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-black text-slate-200 uppercase tracking-tight">{agent.name}</h4>
                  <p className="text-[10px] text-slate-500 uppercase tracking-widest line-clamp-1">{agent.purpose}</p>
                </div>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                   <span className="text-xs">→</span>
                </div>
              </div>
            </div>
          ))}
          {(!agents || agents.length === 0) && (
            <div className="p-10 text-center border-2 border-dashed border-slate-800 rounded-3xl text-slate-600 text-xs font-bold uppercase tracking-widest">
              Nenhum agente <br/> registrado no V3.
            </div>
          )}
        </div>

        {/* Editor / Visualizador */}
        <div className="lg:col-span-2">
          {selectedAgent ? (
            <div key={selectedAgent.name || 'new'} className="bg-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl animate-in fade-in zoom-in-95 duration-300">
              <div className="flex justify-between items-start mb-10">
                <div className="flex gap-6 items-center">
                  <div className="w-20 h-20 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-2xl shadow-inner">
                    🤖
                  </div>
                  <div>
                    <h2 className="text-2xl font-black italic tracking-tighter uppercase">{selectedAgent.name || 'Novo Agente'}</h2>
                    <p className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest">Configuração Cognitiva</p>
                  </div>
                </div>
                {!isEditing && (
                  <div className="flex gap-3">
                    <button 
                      onClick={() => setIsEditing(true)}
                      className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 text-[10px] font-black uppercase tracking-widest rounded-lg border border-slate-800 transition-all"
                    >
                      Editar 🛠️
                    </button>
                    <button 
                      onClick={() => handleDelete(selectedAgent.name)}
                      className="px-4 py-2 bg-red-900/10 hover:bg-red-900/20 text-red-500 text-[10px] font-black uppercase tracking-widest rounded-lg border border-red-900/20 transition-all"
                    >
                      Remover 🗑️
                    </button>
                  </div>
                )}
              </div>

              <form onSubmit={handleSave} className="space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Identificador Único</label>
                    <input 
                      name="name"
                      defaultValue={selectedAgent.name} 
                      readOnly={!isEditing}
                      required
                      placeholder="EX: AGENT_RESEARCHER"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-bold uppercase focus:outline-none focus:border-indigo-500 transition-all"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Propósito / Especialidade</label>
                    <input 
                      name="purpose"
                      defaultValue={selectedAgent.purpose} 
                      readOnly={!isEditing}
                      required
                      placeholder="EX: Pesquisa de mercado autônoma"
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs focus:outline-none focus:border-indigo-500 transition-all"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">System Prompt (O Cérebro)</label>
                  <textarea 
                    name="system_prompt"
                    defaultValue={selectedAgent.system_prompt} 
                    readOnly={!isEditing}
                    required
                    rows={8}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-mono focus:outline-none focus:border-indigo-500 transition-all resize-none"
                    placeholder="Defina as diretrizes, limitações e tom de voz do agente..."
                  />
                </div>

                <div className="space-y-4">
                  <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Ferramentas Ativas (Tools)</label>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className={`flex items-center gap-4 p-4 border rounded-xl transition-all cursor-pointer ${selectedAgent.tools?.includes('google_search') ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-slate-800 bg-slate-900'}`}>
                      <input 
                        type="checkbox" 
                        name="tool_google_search" 
                        disabled={!isEditing}
                        defaultChecked={selectedAgent.tools?.includes('google_search')}
                        className="w-4 h-4 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-offset-slate-950"
                      />
                      <div>
                        <p className="text-xs font-bold text-slate-200 uppercase tracking-tight">Google Search</p>
                        <p className="text-[9px] text-slate-500 uppercase tracking-widest">Navegação em tempo real</p>
                      </div>
                    </label>
                  </div>
                </div>

                {isEditing && (
                  <div className="flex gap-4 pt-4">
                    <button 
                      type="submit"
                      disabled={saveAgent.isLoading}
                      className="flex-1 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all shadow-lg"
                    >
                      {saveAgent.isLoading ? 'Salvando...' : 'Gravar Alterações 💾'}
                    </button>
                    <button 
                      type="button"
                      onClick={() => { setIsEditing(false); if (!selectedAgent.name) setSelectedAgent(null); }}
                      className="px-10 bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold text-xs uppercase tracking-widest rounded-xl transition-all"
                    >
                      Cancelar
                    </button>
                  </div>
                )}
              </form>
            </div>
          ) : (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-950/20 border-2 border-dashed border-slate-800 rounded-3xl p-10 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
              <div className="text-6xl mb-6">🤖</div>
              <h3 className="text-sm font-black italic tracking-tighter uppercase text-slate-400">Cognição não selecionada</h3>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest font-bold mt-2">Escolha um agente para visualizar ou editar seu núcleo neural</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentsPage;
