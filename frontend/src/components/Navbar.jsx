import React from 'react';
import { LayoutDashboard, Terminal, LogOut, Shield, User } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, user, onLogout }) {
  return (
    <nav className="glass-panel" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '16px 24px',
      margin: '20px',
      borderRadius: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-pink) 100%)',
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '20px',
          boxShadow: 'var(--neon-shadow-purple)'
        }}>
          Ω
        </div>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: '800', fontFamily: 'var(--font-heading)' }} className="gradient-text">
            AI FinOps Gateway
          </h1>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            v1.0.0 · Enterprise Gateway
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        {user.role !== 'admin' && (
          <button
            onClick={() => setActiveTab('playground')}
            className={`btn-secondary ${activeTab === 'playground' ? 'active-tab' : ''}`}
            style={{
              padding: '10px 18px',
              fontSize: '14px',
              backgroundColor: activeTab === 'playground' ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
              borderColor: activeTab === 'playground' ? 'var(--accent-purple)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Terminal size={16} color={activeTab === 'playground' ? 'var(--accent-purple)' : 'var(--text-secondary)'} />
            AI Playground
          </button>
        )}

        {user.role === 'admin' && (
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`btn-secondary ${activeTab === 'dashboard' ? 'active-tab' : ''}`}
            style={{
              padding: '10px 18px',
              fontSize: '14px',
              backgroundColor: activeTab === 'dashboard' ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
              borderColor: activeTab === 'dashboard' ? 'var(--accent-cyan)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <LayoutDashboard size={16} color={activeTab === 'dashboard' ? 'var(--accent-cyan)' : 'var(--text-secondary)'} />
            FinOps Dashboard
          </button>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: '20px',
          background: 'rgba(255, 255, 255, 0.05)',
          fontSize: '13px',
          border: '1px solid var(--glass-border)'
        }}>
          {user.role === 'admin' ? (
            <>
              <Shield size={14} color="var(--accent-pink)" />
              <span style={{ color: 'var(--accent-pink)', fontWeight: 'bold' }}>Admin</span>
            </>
          ) : (
            <>
              <User size={14} color="var(--accent-cyan)" />
              <span style={{ color: 'var(--accent-cyan)' }}>{user.username}</span>
            </>
          )}
        </div>

        <button
          onClick={onLogout}
          className="btn-secondary"
          style={{
            padding: '10px',
            borderRadius: '10px',
            borderColor: 'rgba(239, 68, 68, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Cerrar sesión"
        >
          <LogOut size={16} color="var(--color-error)" />
        </button>
      </div>
    </nav>
  );
}
