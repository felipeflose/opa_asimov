import { useState, useRef, useEffect } from 'react';
import apiClient from '../../api/client';

const ChatWidget = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input.trim() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            // Prepara histórico para o BFF V3 (max 4 últimas)
            const history = messages.slice(-4).map(m => ({ 
                role: m.role, 
                content: m.content 
            }));

            const { data } = await apiClient.post('/api/chat/', {
                message: userMsg.content,
                history: history
            });

            const aiMsg = { role: 'assistant', content: data.response };
            setMessages(prev => [...prev, aiMsg]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'system', content: 'Erro na orquestração: ' + (err.response?.data?.detail || 'Offline') }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-8 right-8 w-[400px] h-[600px] bg-slate-950/95 backdrop-blur-xl border border-slate-800 rounded-3xl shadow-2xl flex flex-col overflow-hidden z-[100] animate-in slide-in-from-bottom-10 fade-in duration-500">
            {/* Header */}
            <div className="p-6 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-4 h-4 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                    <h3 className="text-sm font-black italic tracking-tighter uppercase text-slate-200">Orquestrador Central v3</h3>
                </div>
            </div>

            {/* Messages */}
            <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center opacity-30 grayscale hover:grayscale-0 transition-all">
                        <span className="text-4xl mb-4">🧠</span>
                        <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Núcleo Cognitivo Online.<br/>Como posso atuar hoje?</p>
                    </div>
                )}
                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
                        <div className={`max-w-[85%] p-4 rounded-2xl text-xs font-medium leading-relaxed
                            ${m.role === 'user' 
                                ? 'bg-indigo-600/90 text-white rounded-tr-sm shadow-indigo-500/10 shadow-lg' 
                                : m.role === 'system'
                                    ? 'bg-red-900/10 text-red-500 border border-red-900/20 italic'
                                    : 'bg-slate-900/80 text-slate-300 border border-slate-800 rounded-tl-sm shadow-sm'
                            }
                        `}>
                            {m.content}
                        </div>
                    </div>
                ))}
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-6 bg-slate-900/30 border-t border-slate-800">
                <div className="relative group">
                    <input 
                        className="w-full bg-slate-950/50 border border-slate-800/80 group-hover:border-indigo-500/30 rounded-2xl py-4 pl-5 pr-12 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500/20 transition-all placeholder-slate-600"
                        placeholder="Digite sua ordem ou pergunta..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />
                    <button 
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center hover:bg-indigo-500 disabled:opacity-30 transition-all shadow-lg active:scale-90"
                    >
                        {loading ? '⚡' : '→'}
                    </button>
                </div>
                <p className="text-[8px] text-slate-600 text-center uppercase font-black tracking-widest mt-3 opacity-50">v3.0 Cognition Hub — SSE Supported</p>
            </form>
        </div>
    );
};

export default ChatWidget;
