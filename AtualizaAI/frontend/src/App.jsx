import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './store/useAuthStore';
import './index.css';

// Layout e Paginas (V3 Structure)
import DashboardPage from './pages/Dashboard';
import AgentsPage from './pages/Agents';
import TasksPage from './pages/Tasks';
import FinOpsPage from './pages/FinOps';
import LoginPage from './pages/Login';
import Sidebar from './components/Sidebar';

// Cliente de Dados V3
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Auth Guard V3
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

function AppV3() {
  const { isAuthenticated } = useAuthStore();

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-slate-900 text-slate-100 font-sans">
          {isAuthenticated && <Sidebar />}
          
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Private Routes (V3 BFF) */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/agents" 
                element={
                  <ProtectedRoute>
                    <AgentsPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/tasks" 
                element={
                  <ProtectedRoute>
                    <TasksPage />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/finops" 
                element={
                  <ProtectedRoute>
                    <FinOpsPage />
                  </ProtectedRoute>
                } 
              />
              
              {/* Fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default AppV3;
