import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useAgents, useSaveAgent } from '../api/hooks/useAgents';

const ClassroomPage = () => {
  const queryClient = useQueryClient();
  const { data: agents, isLoading } = useAgents();
  const saveAgent = useSaveAgent();
  
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [activeTab, setActiveTab] = useState('config'); // 'config', 'training', 'rag'

  if (isLoading) return <div className="p-10 text-purple-400 font-black animate-pulse">📚 ABRINDO SALA DE AULA...</div>;

  const trainingAgents = agents?.filter(a => a.status === 'in_training') || [];

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedAgent?.name) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      await apiClient.post(`/api/agents/${selectedAgent.name}/upload`, formData);
      queryClient.invalidateQueries(['agents']);
      alert('Arquivo de conhecimento enviado para o bucket! 📄');
    } catch (err) {
      alert('Erro no upload: ' + err.message);
    }
  };

  const handleAddLink = async () => {
    const link = prompt('Insira a URL do site para o agente ler:');
    if (!link || !selectedAgent?.name) return;
    try {
      await apiClient.post(`/api/agents/${selectedAgent.name}/link`, { link });
      queryClient.invalidateQueries(['agents']);
      alert('Link aprendido e salvo no cache! 🔗');
    } catch (err) {
      alert('Erro ao adicionar link: ' + err.message);
    }
  };

  const handlePromote = async (agent) => {
    if (agent.training_progress < 100) {
      alert('O agente precisa de 100% de progresso para se formar!');
      return;
    }
    try {
      const updated = { ...agent, status: 'ready' };
      await saveAgent.mutateAsync(updated);
      setSelectedAgent(null);
      alert(`${agent.name} se formou e agora está na Biblioteca de Agentes! 🎓🚀`);
    } catch (err) {
      alert('Erro ao promover agente: ' + err.message);
    }
  };

  const handleUpdateProgress = (e) => {
    const val = parseInt(e.target.value);
    setSelectedAgent({ ...selectedAgent, training_progress: val });
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500 pb-20">
      <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-purple-500/20 shadow-xl">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent uppercase">
            SALA DE AULA
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Calibração e Treinamento de Redes Neurais</p>
        </div>
        <div className="px-6 py-2 bg-purple-900/10 border border-purple-500/20 rounded-xl">
           <span className="text-purple-400 font-black text-xl">{trainingAgents.length}</span>
           <span className="ml-2 text-[10px] text-slate-500 font-bold uppercase tracking-widest">Alunos em Treino</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Lista de Alunos */}
        <div className="lg:col-span-1 space-y-4 max-h-[75vh] overflow-y-auto pr-2 custom-scrollbar">
          {trainingAgents.map((agent) => (
            <div 
              key={agent.name}
              onClick={() => { setSelectedAgent(agent); setActiveTab('config'); }}
              className={`p-5 bg-slate-950 border rounded-2xl cursor-pointer transition-all group ${selectedAgent?.name === agent.name ? 'border-purple-500/50 bg-purple-500/5 shadow-lg shadow-purple-500/5' : 'border-slate-800 hover:border-slate-700'}`}
            >
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-black text-slate-200 uppercase tracking-tight">{agent.name}</h4>
                  <span className="text-[10px] font-black text-purple-400">{agent.training_progress}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-purple-600 to-pink-600 transition-all duration-500" style={{ width: `${agent.training_progress}%` }} />
                </div>
              </div>
            </div>
          ))}
          {trainingAgents.length === 0 && (
            <div className="p-10 text-center border-2 border-dashed border-slate-800 rounded-3xl text-slate-600 text-xs font-bold uppercase tracking-widest">
              Todos os agentes <br/> estão formados! 🎉
            </div>
          )}
        </div>

        {/* Mesa do Professor */}
        <div className="lg:col-span-2">
          {selectedAgent ? (
            <div key={selectedAgent.name} className="bg-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl animate-in fade-in zoom-in-95 duration-300">
              <div className="flex justify-between items-center mb-8 pb-6 border-b border-slate-800/50">
                 <div className="flex gap-4 items-center">
                   <div className="w-14 h-14 rounded-full bg-purple-600/10 border border-purple-500/30 flex items-center justify-center text-2xl shadow-inner">🎓</div>
                   <div>
                     <h2 className="text-xl font-black italic tracking-tighter uppercase leading-none">{selectedAgent.name}</h2>
                     <p className="text-[10px] text-purple-500 font-bold uppercase tracking-widest mt-1">Status: Calibração v3.0</p>
                   </div>
                 </div>
                 <button 
                  onClick={() => handlePromote(selectedAgent)}
                  className={`px-8 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${selectedAgent.training_progress === 100 ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 active:scale-95' : 'bg-slate-800 text-slate-600 cursor-not-allowed'}`}
                 >
                   Promover para Produção 🚀
                 </button>
              </div>

              {/* TABS DE TREINAMENTO */}
              <div className="flex gap-8 mb-8 border-b border-slate-800/50 pb-px">
                {['config', 'rag', 'training'].map((tab) => (
                  <button 
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`pb-4 px-1 text-[10px] font-black uppercase tracking-widest transition-all border-b-2 ${activeTab === tab ? 'border-purple-500 text-purple-400' : 'border-transparent text-slate-600 hover:text-slate-400'}`}
                  >
                    {tab === 'config' ? '🧠 Cérebro (Prompt)' : tab === 'rag' ? '📚 Conhecimento (RAG)' : '📈 Evolução'}
                  </button>
                ))}
              </div>

              <div className="min-h-[400px]">
                {activeTab === 'config' && (
                  <div className="space-y-6 animate-in fade-in duration-300">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest block">System Prompt (Personalidade)</label>
                        <span className="text-[8px] text-slate-700 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">Markdown Aceito</span>
                      </div>
                      <textarea 
                        value={selectedAgent.system_prompt}
                        onChange={(e) => setSelectedAgent({...selectedAgent, system_prompt: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 text-xs font-mono min-h-[250px] focus:border-purple-500/50 outline-none text-slate-300 transition-colors"
                        placeholder="Descreva aqui como o agente deve agir..."
                      />
                    </div>
                    <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl">
                      <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-4 block">Habilidades & Ferramentas</label>
                      <button 
                        onClick={() => {
                          const tools = selectedAgent.tools || [];
                          const next = tools.includes('google_search') ? tools.filter(t => t !== 'google_search') : [...tools, 'google_search'];
                          setSelectedAgent({...selectedAgent, tools: next});
                        }}
                        className={`group flex items-center gap-3 px-6 py-3 rounded-xl border text-[10px] font-black uppercase tracking-tight transition-all ${selectedAgent.tools?.includes('google_search') ? 'bg-green-500/10 border-green-500/40 text-green-400' : 'bg-slate-800 border-slate-700 text-slate-500 hover:border-slate-600'}`}
                      >
                        <span className={`text-sm ${selectedAgent.tools?.includes('google_search') ? 'animate-pulse' : ''}`}>🌐</span> 
                        Google Search (Grounding) 
                        <span className={`ml-2 px-2 py-0.5 rounded ${selectedAgent.tools?.includes('google_search') ? 'bg-green-500 text-slate-950' : 'bg-slate-700 text-slate-500'}`}>
                          {selectedAgent.tools?.includes('google_search') ? 'ATIVO' : 'OFF'}
                        </span>
                      </button>
                    </div>
                  </div>
                )}

                {activeTab === 'rag' && (
                  <div className="space-y-8 animate-in fade-in duration-300">
                    <div className="grid grid-cols-2 gap-6">
                        <div className="p-10 bg-slate-900/50 border-2 border-dashed border-slate-800 rounded-3xl text-center group hover:border-purple-500/30 transition-all cursor-pointer">
                          <input type="file" id="fileTrain" className="hidden" onChange={handleFileUpload} />
                          <label htmlFor="fileTrain" className="cursor-pointer">
                            <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">📄</div>
                            <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Anexar Documento</p>
                            <p className="text-[8px] text-slate-600 mt-2 uppercase font-bold tracking-tight">PDF, TXT, JSON (Bucket GCS)</p>
                          </label>
                        </div>
                        <div 
                          onClick={handleAddLink}
                          className="p-10 bg-slate-900/50 border-2 border-dashed border-slate-800 rounded-3xl text-center cursor-pointer group hover:border-purple-500/30 transition-all"
                        >
                          <div className="text-4xl mb-4 group-hover:scale-110 transition-transform">🔗</div>
                          <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Adicionar Link</p>
                          <p className="text-[8px] text-slate-600 mt-2 uppercase font-bold tracking-tight">Scraping Automático & Cache 🏛️</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="flex justify-between items-center bg-slate-900 p-4 rounded-xl border border-slate-800">
                          <h4 className="text-[10px] text-purple-400 font-black uppercase tracking-widest">Conhecimento Adquirido</h4>
                          <span className="text-[10px] text-slate-600 font-black">{(selectedAgent.rag?.files?.length || 0) + (selectedAgent.rag?.links?.length || 0)} Itens</span>
                        </div>
                        <div className="grid grid-cols-1 gap-2 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                          {selectedAgent.rag?.files?.map((file, i) => (
                            <div key={i} className="flex items-center gap-3 p-4 bg-slate-900/30 border border-slate-800 rounded-xl text-[10px]">
                              <span className="text-slate-500">📄</span>
                              <span className="text-slate-400 truncate flex-1">{file}</span>
                              <span className="text-[8px] text-slate-700 uppercase font-black">Arquivo</span>
                            </div>
                          ))}
                          {selectedAgent.rag?.links?.map((link, i) => (
                            <div key={i} className="flex items-center gap-3 p-4 bg-slate-900/30 border border-slate-800 rounded-xl text-[10px]">
                              <span className="text-indigo-400">🔗</span>
                              <span className="text-slate-400 truncate flex-1">{link}</span>
                              <span className="text-[8px] text-indigo-900 uppercase font-black">Site</span>
                            </div>
                          ))}
                          {(!selectedAgent.rag?.files?.length && !selectedAgent.rag?.links?.length) && (
                            <div className="py-10 text-center text-slate-700 text-[10px] font-black uppercase tracking-tight italic">
                              Nenhum conhecimento externo ainda...
                            </div>
                          )}
                        </div>
                    </div>
                  </div>
                )}

                {activeTab === 'training' && (
                  <div className="space-y-10 animate-in fade-in duration-300">
                    <div className="p-8 bg-slate-900/50 border border-slate-800 rounded-3xl">
                      <div className="flex justify-between mb-6 items-end">
                        <div>
                          <label className="text-[10px] text-slate-400 uppercase font-black tracking-widest block mb-1">Nível de Maturidade Neuronal</label>
                          <p className="text-[9px] text-slate-600 uppercase font-bold">Arraste para atualizar o progresso</p>
                        </div>
                        <span className="text-4xl font-black text-purple-400 tracking-tighter">{selectedAgent.training_progress}%</span>
                      </div>
                      <input 
                        type="range" min="0" max="100" 
                        value={selectedAgent.training_progress} 
                        onChange={handleUpdateProgress}
                        className="w-full h-3 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500 shadow-inner"
                      />
                      <div className="flex justify-between mt-4 text-[9px] text-slate-600 font-black uppercase tracking-widest">
                        <span>🐣 Iniciante</span>
                        <span>🧠 Treinado</span>
                        <span>🎓 Formado (100%)</span>
                      </div>
                    </div>

                    <div className="space-y-4">
                        <h4 className="text-[10px] text-slate-500 font-black uppercase tracking-widest flex items-center gap-2">
                           <div className="w-1 h-1 bg-purple-500 rounded-full animate-ping" />
                           Checklist de Formatura
                        </h4>
                        <div className="grid grid-cols-1 gap-3">
                          {[
                            { label: 'System Prompt (Instruções Base)', reached: !!selectedAgent.system_prompt },
                            { label: 'RAG: Documentos (PDF/TXT/JSON)', reached: selectedAgent.rag?.files?.length > 0 },
                            { label: 'RAG: Links Externos (Web)', reached: selectedAgent.rag?.links?.length > 0 },
                            { label: 'Ferramentas de Busca (Grounding)', reached: selectedAgent.tools?.includes('google_search') }
                          ].map((check, i) => (
                            <div key={i} className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${check.reached ? 'bg-green-500/5 border-green-500/20' : 'bg-slate-900/30 border-slate-800'}`}>
                              <span className={`text-[11px] font-bold ${check.reached ? 'text-green-400' : 'text-slate-500'}`}>{check.label}</span>
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${check.reached ? 'bg-green-500/20 text-green-400' : 'bg-slate-800 text-slate-700'}`}>
                                {check.reached ? '✓' : '○'}
                              </div>
                            </div>
                          ))}
                        </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-8 mt-8 border-t border-slate-800/50">
                <button 
                  onClick={async () => {
                    await saveAgent.mutateAsync(selectedAgent);
                    queryClient.invalidateQueries(['agents']);
                    alert('Conhecimento e Progresso salvos no GCS! 💾✅');
                  }}
                  className="w-full py-5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-black text-xs uppercase tracking-widest rounded-2xl shadow-xl shadow-purple-900/20 transition-all active:scale-[0.98]"
                >
                  Salvar Treinamento do Agente 💾
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[500px] flex flex-col items-center justify-center bg-slate-950/20 border-2 border-dashed border-slate-800 rounded-3xl p-10 opacity-50 grayscale">
              <div className="text-8xl mb-8 animate-bounce">🎓</div>
              <h3 className="text-xl font-black italic tracking-tighter uppercase text-slate-400">Sala de Aula Vazia</h3>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest font-black mt-3 text-center leading-relaxed">
                Selecione um aluno na lista ao lado <br/> para iniciar a calibração neuronal v3.0
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClassroomPage;
