import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

const Sidebar = () => {
  const { logout, adminEmail } = useAuthStore();

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
    { id: 'agents', label: 'Agentes', icon: '🤖', path: '/agents' },
    { id: 'tasks', label: 'Demandas', icon: '📋', path: '/tasks' },
    { id: 'finops', label: 'FinOps', icon: '💎', path: '/finops' },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col pt-8 pb-4">
      <div className="px-6 mb-10 text-center">
        <h1 className="text-2xl font-black italic tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          FLOSE AI
        </h1>
        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mt-1">Platform v3.0</p>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {menuItems.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) => `
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group
              ${isActive ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30' : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'}
            `}
          >
            <span className="text-xl group-hover:scale-110 transition-transform">{item.icon}</span>
            <span className="font-semibold">{item.label}</span>
            <div className="ml-auto w-1 h-1 rounded-full bg-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </NavLink>
        ))}
      </nav>

      <div className="px-4 mt-auto">
        <div className="bg-slate-900/50 p-4 rounded-2xl border border-slate-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center font-bold text-xs">
              {adminEmail?.charAt(0).toUpperCase() || 'A'}
            </div>
            <div className="truncate">
              <p className="text-xs font-bold truncate">{adminEmail || 'Admin'}</p>
              <p className="text-[9px] text-slate-500 uppercase tracking-tight">Privileged Access</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="w-full py-2 bg-slate-800 hover:bg-red-900/20 hover:text-red-400 text-slate-400 text-xs font-bold rounded-lg border border-slate-700 hover:border-red-900/50 transition-all"
          >
            Sair do Sistema 🚪
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
