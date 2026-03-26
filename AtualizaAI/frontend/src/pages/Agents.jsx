import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../client';
import { useAgents, useSaveAgent, useDeleteAgent } from '../api/hooks/useAgents';

const AgentsPage = () => {
  const queryClient = useQueryClient();
  const { data: agents, isLoading } = useAgents();
  const saveAgent = useSaveAgent();
  const deleteAgent = useDeleteAgent();
  
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('config'); // 'config' ou 'rag'

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !selectedAgent?.name) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await apiClient.post(`/api/agents/${selectedAgent.name}/upload`, formData);
      alert('Arquivo enviado com sucesso!');
      queryClient.invalidateQueries(['agents']);
    } catch (err) {
      alert('Erro no upload: ' + err.message);
    }
  };

  const handleAddLink = async () => {
    const link = prompt('Insira a URL do link:');
    if (!link || !selectedAgent?.name) return;
    
    try {
      const formData = new FormData();
      formData.append('link', link);
      await apiClient.post(`/api/agents/${selectedAgent.name}/link`, formData);
      queryClient.invalidateQueries(['agents']);
    } catch (err) {
      alert('Erro ao adicionar link: ' + err.message);
    }
  };

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
        tools: tools,
        rag: selectedAgent.rag || { files: [], links: [] }
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
          onClick={() => { setSelectedAgent({ rag: { files: [], links: [] } }); setIsEditing(true); setActiveTab('config'); }}
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
              onClick={() => { setSelectedAgent(agent); setIsEditing(false); setActiveTab('config'); }}
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
              <div className="flex justify-between items-start mb-6">
                <div className="flex gap-6 items-center">
                  <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-xl shadow-inner">
                    🤖
                  </div>
                  <div>
                    <h2 className="text-xl font-black italic tracking-tighter uppercase">{selectedAgent.name || 'Novo Agente'}</h2>
                    <div className="flex gap-4 mt-2">
                      <button 
                        onClick={() => setActiveTab('config')}
                        className={`text-[9px] font-black uppercase tracking-widest pb-1 border-b-2 transition-all ${activeTab === 'config' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-600 hover:text-slate-400'}`}
                      >
                        🧠 Configuração
                      </button>
                      <button 
                        onClick={() => setActiveTab('rag')}
                        className={`text-[9px] font-black uppercase tracking-widest pb-1 border-b-2 transition-all ${activeTab === 'rag' ? 'border-purple-500 text-purple-400' : 'border-transparent text-slate-600 hover:text-slate-400'}`}
                      >
                        📚 Conhecimento (RAG)
                      </button>
                    </div>
                  </div>
                </div>
                {!isEditing && (
                  <div className="flex gap-2">
                    <button onClick={() => setIsEditing(true)} className="p-2 bg-slate-900 hover:bg-slate-800 text-slate-400 rounded-lg border border-slate-800 transition-all text-[10px]">🛠️</button>
                    <button onClick={() => handleDelete(selectedAgent.name)} className="p-2 bg-red-900/10 hover:bg-red-900/20 text-red-500 rounded-lg border border-red-900/20 transition-all text-[10px]">🗑️</button>
                  </div>
                )}
              </div>

              {activeTab === 'config' ? (
                <form onSubmit={handleSave} className="space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Identificador Único</label>
                      <input name="name" defaultValue={selectedAgent.name} readOnly={!isEditing} required className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-bold uppercase focus:outline-none focus:border-indigo-500" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Propósito / Especialidade</label>
                      <input name="purpose" defaultValue={selectedAgent.purpose} readOnly={!isEditing} required className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs focus:outline-none focus:border-indigo-500" />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">System Prompt (O Cérebro)</label>
                    <textarea name="system_prompt" defaultValue={selectedAgent.system_prompt} readOnly={!isEditing} required rows={6} className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-xs font-mono focus:outline-none focus:border-indigo-500 resize-none" />
                  </div>

                  <div className="space-y-4">
                    <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Ferramentas Ativas</label>
                    <div className="grid grid-cols-2 gap-4">
                      <label className={`flex items-center gap-3 p-3 border rounded-xl cursor-pointer ${selectedAgent.tools?.includes('google_search') ? 'border-indigo-500/50 bg-indigo-500/5' : 'border-slate-800 bg-slate-900'}`}>
                        <input type="checkbox" name="tool_google_search" disabled={!isEditing} defaultChecked={selectedAgent.tools?.includes('google_search')} className="rounded border-slate-700 bg-slate-800 text-indigo-600" />
                        <span className="text-[10px] font-bold text-slate-300 uppercase">Google Search</span>
                      </label>
                    </div>
                  </div>

                  {isEditing && (
                    <div className="flex gap-4 pt-4">
                      <button type="submit" className="flex-1 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all shadow-lg">Gravar Alterações 💾</button>
                      <button type="button" onClick={() => { setIsEditing(false); if (!selectedAgent.name) setSelectedAgent(null); }} className="px-10 bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold text-xs uppercase tracking-widest rounded-xl transition-all">Cancelar</button>
                    </div>
                  )}
                </form>
              ) : (
                <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div className="grid grid-cols-2 gap-8">
                    {/* Documentos */}
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Documentos (PDF/TXT/DOCX)</label>
                        <input type="file" id="rag-upload" className="hidden" onChange={handleFileUpload} />
                        <label htmlFor="rag-upload" className="px-3 py-1 bg-purple-600 hover:bg-purple-500 text-white text-[9px] font-black uppercase rounded-lg cursor-pointer transition-all">Upload +</label>
                      </div>
                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 min-h-[150px] space-y-2">
                        {selectedAgent.rag?.files?.map((file, i) => (
                          <div key={i} className="flex justify-between items-center p-2 bg-slate-950 border border-slate-800 rounded-lg group">
                            <span className="text-[10px] text-slate-400 truncate max-w-[150px]">{file.split('/').pop()}</span>
                            <span className="text-[8px] text-slate-600 uppercase font-bold">GCS Storage</span>
                          </div>
                        ))}
                        {(!selectedAgent.rag?.files || selectedAgent.rag.files.length === 0) && (
                          <p className="text-[10px] text-slate-600 italic text-center py-10">Nenhum documento anexado.</p>
                        )}
                      </div>
                    </div>

                    {/* Links */}
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest">Links Externos (URLs)</label>
                        <button onClick={handleAddLink} className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-[9px] font-black uppercase rounded-lg transition-all">Adicionar +</button>
                      </div>
                      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 min-h-[150px] space-y-2">
                        {selectedAgent.rag?.links?.map((link, i) => (
                          <div key={i} className="flex justify-between items-center p-2 bg-slate-950 border border-slate-800 rounded-lg">
                            <span className="text-[10px] text-slate-400 truncate max-w-[150px]">{link}</span>
                            <a href={link} target="_blank" rel="noreferrer" className="text-[9px] text-indigo-500 hover:text-indigo-400 font-bold">Acessar</a>
                          </div>
                        ))}
                        {(!selectedAgent.rag?.links || selectedAgent.rag.links.length === 0) && (
                          <p className="text-[10px] text-slate-600 italic text-center py-10">Nenhum link adicionado.</p>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-purple-900/10 border border-purple-900/20 rounded-2xl">
                    <p className="text-[10px] text-purple-400 font-bold uppercase tracking-tight mb-2">💡 Como funciona o RAG V3?</p>
                    <p className="text-[9px] text-slate-500 leading-relaxed uppercase tracking-wider">Os arquivos e links anexados formam a "Base de Conhecimento" desse agente. Ao ser acionado na orquestração, ele consultará prioritariamente essas fontes antes de responder ao usuário.</p>
                  </div>
                </div>
              )}
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
