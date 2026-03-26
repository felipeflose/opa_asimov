import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import apiClient from '../api/client';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const { data } = await apiClient.post('/api/auth/login', { email, password });
      login(data.token, data.admin_email);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao realizar login. Verifique as credenciais.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 overflow-hidden relative">
      {/* Background Decor */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[100px] rounded-full" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-purple-600/10 blur-[100px] rounded-full" />
      
      <div className="w-full max-w-md p-10 bg-slate-950 rounded-3xl border border-slate-800 shadow-2xl relative z-10">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-black italic tracking-tighter bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            FLOSE AI v3.1 🚀
          </h1>
          <p className="text-xs text-slate-500 uppercase tracking-widest font-bold mt-2">v3.0 Cognition Hub</p>
        </div>

        {error && (
          <div className="p-4 mb-6 bg-red-900/20 border border-red-900/50 rounded-xl text-red-500 text-xs font-bold text-center">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-6">
          <div className="space-y-2">
            <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Admin E-mail</label>
            <input 
              type="email" 
              required
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all"
              placeholder="seu-email@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] text-slate-500 uppercase font-black tracking-widest pl-1">Master Password</label>
            <input 
              type="password" 
              required
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-4 text-sm focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button 
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-black text-sm uppercase tracking-widest rounded-xl transition-all shadow-lg active:scale-95 disabled:opacity-50"
          >
            {loading ? 'Autenticando...' : 'Desbloquear V3 🚀'}
          </button>
        </form>

        <p className="mt-8 text-center text-[10px] text-slate-600 uppercase tracking-tight">
          Protegido por Criptografia de Ponta-a-Ponta
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
