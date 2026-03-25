import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/client';

const TasksPage = () => {
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/tasks/');
      return data;
    }
  });

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }) => {
      await apiClient.patch(`/api/tasks/${id}/status?new_status=${status}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }
  });

  const createTask = useMutation({
    mutationFn: async (task) => {
      const { data } = await apiClient.post('/api/tasks/', task);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setIsAdding(false);
    }
  });

  const columns = ['Aberto', 'Em Execução', 'Finalizado', 'Pausado'];

  if (isLoading) return <div className="p-10 text-indigo-400">⚡ Sincronizando Kanban...</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex justify-between items-center bg-slate-950/40 p-8 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent uppercase">
             Kanban de Demandas
          </h1>
          <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px] mt-1">Gestão de TRDs e entregas v3.0</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="px-8 py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-black uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95"
        >
          Nova Demanda +
        </button>
      </header>

      {isAdding && (
        <div className="p-8 bg-slate-950 border border-slate-800 rounded-3xl animate-in zoom-in-95 duration-300">
          <form onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            createTask.mutate({ title: fd.get('title'), description: fd.get('description'), priority: fd.get('priority') });
          }} className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <input name="title" required placeholder="Título da Demanda" className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-xs uppercase font-bold focus:outline-none focus:border-blue-500 transition-all"/>
              <select name="priority" className="bg-slate-900 border border-slate-800 p-4 rounded-xl text-xs font-bold focus:outline-none focus:border-blue-500 transition-all">
                <option>Baixa</option>
                <option>Média</option>
                <option>Alta</option>
              </select>
            </div>
            <textarea name="description" required rows={3} placeholder="Descrição detalhada..." className="w-full bg-slate-900 border border-slate-800 p-4 rounded-xl text-xs focus:outline-none focus:border-blue-500 transition-all resize-none"/>
            <div className="flex gap-4">
               <button type="submit" className="flex-1 py-4 bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-widest rounded-xl transition-all shadow-lg">Criar Demanda 🚀</button>
               <button type="button" onClick={() => setIsAdding(false)} className="px-10 bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold text-xs uppercase tracking-widest rounded-xl transition-all">Cancelar</button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 min-h-[500px]">
        {columns.map(col => (
          <div key={col} className="bg-slate-900/30 border border-slate-800/50 rounded-3xl p-4 flex flex-col">
            <div className="px-4 py-2 border-b border-slate-800 mb-4 flex justify-between items-center">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">{col}</span>
              <span className="w-5 h-5 bg-slate-800 rounded-full flex items-center justify-center text-[10px] font-bold text-slate-400">
                {tasks?.filter(t => t.status === col).length || 0}
              </span>
            </div>
            
            <div className="flex-1 space-y-4 overflow-y-auto max-h-[600px] pr-1">
              {tasks?.filter(t => t.status === col).map(task => (
                <div key={task.id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl group hover:border-blue-500/30 transition-all shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[8px] bg-slate-900 px-2 py-1 rounded text-slate-500 font-bold uppercase tracking-tight">{task.id}</span>
                    <span className={`text-[8px] px-2 py-1 rounded font-bold uppercase ${task.priority === 'Alta' ? 'bg-red-900/20 text-red-500' : 'bg-slate-800 text-slate-400'}`}>
                      {task.priority}
                    </span>
                  </div>
                  <h4 className="text-xs font-black text-slate-100 uppercase tracking-tight mb-2">{task.title}</h4>
                  <p className="text-[10px] text-slate-500 line-clamp-2 mb-4 leading-relaxed">{task.description}</p>
                  
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-2 border-t border-slate-900">
                    {columns.filter(c => c !== col).map(c => (
                      <button 
                        key={c}
                        onClick={() => updateStatus.mutate({ id: task.id, status: c })}
                        className="flex-1 py-1 px-1 bg-slate-900 hover:bg-slate-800 text-[7px] font-bold uppercase text-slate-400 rounded transition-all"
                      >
                         {c}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TasksPage;
