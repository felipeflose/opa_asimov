import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';
import { useAgents, useSaveAgent } from '../api/hooks/useAgents';

const ClassroomPage = () => {
  const queryClient = useQueryClient();
  const { data: agents, isLoading } = useAgents();
  const saveAgent = useSaveAgent();
  
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [activeTab, setActiveTab] = useState('training');

  if (isLoading) return <div className="p-10 text-purple-400 font-black animate-pulse">📚 ABRINDO SALA DE AULA...</div>;

  const trainingAgents = agents?.filter(a => a.status === 'in_training') || [];

  const handlePromote = async (agent) => {
    if (agent.training_progress < 100) {
      alert('O agente precisa de 100% de progresso para se formar!');
      return;
    }
    
    try {
      const updated = { ...agent, status: 'ready' };
      await saveAgent.mutateAsync(updated);
      setSelectedAgent(null);
      alert(`${agent.name} se formou e agora está na Biblioteca de Agentes! 🎓`);
    } catch (err) {
      alert('Erro ao promover agente: ' + err.message);
    }
  };

  const handleUpdateProgress = async (e) => {
    const val = parseInt(e.target.value);
    const updated = { ...selectedAgent, training_progress: val };
    setSelectedAgent(updated);
  };

  return (
    <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
      <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-purple-500/20 shadow-xl">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            SALA DE AULA (V3.0)
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Calibração e Treinamento de Redes Neurais</p>
        </div>
        <div className="px-6 py-2 bg-purple-900/10 border border-purple-500/20 rounded-xl">
           <span className="text-purple-400 font-black text-xl">{trainingAgents.length}</span>
           <span className="ml-2 text-[10px] text-slate-500 font-bold uppercase tracking-widest">Alunos em Treino</span>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Lista de Alunos (Agentes em Treino) */}
        <div className="lg:col-span-1 space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
          {trainingAgents.map((agent) => (
            <div 
              key={agent.name}
              onClick={() => setSelectedAgent(agent)}
              className={`p-5 bg-slate-950 border rounded-2xl cursor-pointer transition-all group ${selectedAgent?.name === agent.name ? 'border-purple-500/50 bg-purple-500/5' : 'border-slate-800 hover:border-slate-700'}`}
            >
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-black text-slate-200 uppercase tracking-tight">{agent.name}</h4>
                  <span className="text-[10px] font-black text-purple-400">{agent.training_progress}%</span>
                </div>
                {/* Barra de Progresso Mini */}
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

        {/* Mesa do Professor (Editor de Treinamento) */}
        <div className="lg:col-span-2">
          {selectedAgent ? (
            <div key={selectedAgent.name} className="bg-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl animate-in fade-in zoom-in-95 duration-300">
              <div className="flex justify-between items-center mb-8 pb-6 border-b border-slate-800/50">
                 <div className="flex gap-4 items-center">
                   <div className="w-14 h-14 rounded-full bg-purple-600/10 border border-purple-500/30 flex items-center justify-center text-2xl">🎓</div>
                   <div>
                     <h2 className="text-xl font-black italic tracking-tighter uppercase">{selectedAgent.name}</h2>
                     <p className="text-[10px] text-purple-500 font-bold uppercase tracking-widest">Em Fase de Calibração</p>
                   </div>
                 </div>
                 <button 
                  onClick={() => handlePromote(selectedAgent)}
                  className={`px-8 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all ${selectedAgent.training_progress === 100 ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}
                 >
                   Promover para Produção 🚀
                 </button>
              </div>

              <div className="space-y-8">
                {/* Controle de Progresso */}
                <div className="p-6 bg-slate-900/50 border border-slate-800 rounded-2xl">
                  <div className="flex justify-between mb-4">
                    <label className="text-[10px] text-slate-400 uppercase font-black tracking-widest">Progresso do Treinamento</label>
                    <span className="text-xl font-black text-purple-400">{selectedAgent.training_progress}%</span>
                  </div>
                  <input 
                    type="range" min="0" max="100" 
                    value={selectedAgent.training_progress} 
                    onChange={handleUpdateProgress}
                    className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  />
                  <div className="flex justify-between mt-2 text-[8px] text-slate-600 font-bold uppercase tracking-widest">
                    <span>Iniciante</span>
                    <span>Intermediário</span>
                    <span>Especialista (READY)</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {/* Checklist de Treino */}
                  <div className="space-y-4">
                     <h4 className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Checklist de Calibração</h4>
                     <div className="space-y-2">
                        {[
                          { label: 'System Prompt Definido', reached: !!selectedAgent.system_prompt },
                          { label: 'RAG: Documentos Anexados', reached: selectedAgent.rag?.files?.length > 0 },
                          { label: 'RAG: Links de Referência', reached: selectedAgent.rag?.links?.length > 0 },
                          { label: 'Ferramentas (Search) Ativas', reached: selectedAgent.tools?.includes('google_search') }
                        ].map((check, i) => (
                          <div key={i} className="flex items-center gap-3 p-3 bg-slate-900/30 border border-slate-800 rounded-xl">
                            <div className={`w-4 h-4 rounded-full flex items-center justify-center text-[8px] ${check.reached ? 'bg-green-500/20 text-green-400' : 'bg-slate-800 text-slate-600'}`}>
                              {check.reached ? '✓' : '○'}
                            </div>
                            <span className={`text-[10px] font-bold ${check.reached ? 'text-slate-200' : 'text-slate-600'}`}>{check.label}</span>
                          </div>
                        ))}
                     </div>
                  </div>

                  <div className="p-6 bg-indigo-900/10 border border-indigo-900/20 rounded-3xl flex flex-col justify-center text-center">
                    <p className="text-[10px] text-indigo-400 font-black uppercase tracking-widest mb-2">Instruções de Formatura</p>
                    <p className="text-[9px] text-slate-500 leading-relaxed uppercase tracking-widest">
                      O Admin deve validar se o agente responde corretamente no ambiente de teste. Após atingir 100%, clique em promover para que ele apareça na aba principal.
                    </p>
                  </div>
                </div>

                <div className="pt-4">
                  <button 
                    onClick={async () => {
                      await saveAgent.mutateAsync(selectedAgent);
                      queryClient.invalidateQueries(['agents']);
                      alert('Progresso de treinamento salvo!');
                    }}
                    className="w-full py-4 bg-purple-600 hover:bg-purple-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all"
                  >
                    Salvar Evolução Atual 💾
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center bg-slate-950/20 border-2 border-dashed border-slate-800 rounded-3xl p-10 opacity-50 grayscale">
              <div className="text-6xl mb-6">🎓</div>
              <h3 className="text-sm font-black italic tracking-tighter uppercase text-slate-400">Sala de Aula Vazia</h3>
              <p className="text-[10px] text-slate-600 uppercase tracking-widest font-bold mt-2">Selecione um aluno para iniciar a calibração</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClassroomPage;
