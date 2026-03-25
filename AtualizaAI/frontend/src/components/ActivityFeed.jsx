import React, { useEffect, useState } from 'react';

const ActivityFeed = () => {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        const eventSource = new EventSource(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/activity/stream`);

        eventSource.onmessage = (event) => {
            const newEvent = JSON.parse(event.data);
            setEvents(prev => [newEvent, ...prev].slice(0, 10)); // Mantém os 10 mais recentes
        };

        eventSource.onerror = () => {
            console.error('SSE Connection failed. Reconnecting...');
            eventSource.close();
        };

        return () => eventSource.close();
    }, []);

    return (
        <div className="space-y-4">
            {events.length === 0 && (
                <p className="text-[10px] text-slate-600 uppercase tracking-widest text-center py-10 italic">
                    Nenhuma atividade capturada no stream v3...
                </p>
            )}
            {events.map((ev, i) => (
                <div key={ev.id || i} className="flex gap-4 p-4 bg-slate-900/40 rounded-2xl border border-slate-800/50 hover:border-indigo-500/20 transition-all animate-in slide-in-from-right-4 duration-300">
                    <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 shadow-[0_0_10px_rgba(99,102,241,0.5)] animate-pulse" />
                    <div className="flex-1">
                        <p className="text-xs font-bold text-slate-300">{ev.message}</p>
                        <div className="flex justify-between items-center mt-2">
                            <span className="text-[8px] text-slate-500 uppercase tracking-tight font-black">{ev.agent}</span>
                            <span className="text-[8px] text-indigo-500/50 uppercase font-bold">{ev.timestamp}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ActivityFeed;
