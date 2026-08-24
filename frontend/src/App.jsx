import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Playground from './components/Playground';
import Dashboard from './components/Dashboard';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('finops_session');
    return saved ? JSON.parse(saved) : null;
  });
  
  const [activeTab, setActiveTab] = useState(() => {
    const saved = localStorage.getItem('finops_session');
    if (saved) {
      const parsed = JSON.parse(saved);
      return parsed.role === 'admin' ? 'dashboard' : 'playground';
    }
    return 'playground';
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem('finops_session', JSON.stringify(user));
    } else {
      localStorage.removeItem('finops_session');
    }
  }, [user]);

  const handleLogin = (sessionData) => {
    setUser(sessionData);
    setActiveTab(sessionData.role === 'admin' ? 'dashboard' : 'playground');
  };

  const handleLogout = () => {
    setUser(null);
  };

  if (!user) {
    return <Login onLogin={handleLogin} apiUrl={API_URL} />;
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={handleLogout}
      />
      
      <main style={{ flex: 1, padding: '0 20px 40px 20px' }}>
        {activeTab === 'playground' && (
          <Playground user={user} apiUrl={API_URL} />
        )}
        {activeTab === 'dashboard' && (
          <Dashboard user={user} apiUrl={API_URL} />
        )}
      </main>
      
      <footer style={{
        textAlign: 'center',
        padding: '24px',
        color: 'var(--text-muted)',
        fontSize: '12px',
        borderTop: '1px solid var(--glass-border)',
        marginTop: 'auto',
        background: 'rgba(0, 0, 0, 0.1)'
      }}>
        © 2026 AI FinOps Gateway · Desarrollado para la optimización de costes y gobernanza de IA generativa.
      </footer>
    </div>
  );
}

export default App;
