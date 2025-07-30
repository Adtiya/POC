import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import DashboardLayout from './components/layout/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import useAuthStore from './stores/authStore';
import './App.css';

function App() {
  const { initializeAuth } = useAuthStore();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <Router>
      <div className="min-h-screen bg-background">
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          
          {/* Protected routes */}
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="chat" element={<Chat />} />
            <Route path="llm-studio" element={<div className="p-8 text-center">LLM Studio - Coming Soon</div>} />
            <Route path="analytics" element={<div className="p-8 text-center">Analytics - Coming Soon</div>} />
            <Route path="documents" element={<div className="p-8 text-center">Documents - Coming Soon</div>} />
            <Route path="users" element={<div className="p-8 text-center">User Management - Coming Soon</div>} />
            <Route path="security" element={<div className="p-8 text-center">Security - Coming Soon</div>} />
            <Route path="settings" element={<div className="p-8 text-center">Settings - Coming Soon</div>} />
          </Route>
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
