import React, { useState, useEffect } from 'react';
import { Shield, Key, AlertCircle, Users, ShieldAlert } from 'lucide-react';
import { apiFetch } from '../services/apiFetch';

export default function Login({ onLogin, apiUrl }) {
  const [loginMode, setLoginMode] = useState('user'); // 'user' (departments) or 'admin'
  const [consumers, setConsumers] = useState([]);
  const [selectedConsumer, setSelectedConsumer] = useState('');
  
  const [adminUsername, setAdminUsername] = useState('admin');
  const [adminPassword, setAdminPassword] = useState('admin');
  
  const [userPassword, setUserPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchConsumers = async () => {
      try {
        setError(null);
        const response = await apiFetch(`${apiUrl}/v1/admin/consumers`);
        if (response.ok) {
          const data = await response.json();
          setConsumers(data);
          if (data.length > 0) {
            setSelectedConsumer(data[0].id);
            setUserPassword(data[0].id); // Prefill password as same as id for easy mock testing
          }
        } else {
          throw new Error("No se pudieron cargar los departamentos.");
        }
      } catch (err) {
        console.error("Error fetching consumers from proxy:", err);
        setError("Error al conectar con el servidor proxy. Asegúrate de que el backend (FastAPI) esté encendido.");
      }
    };
    fetchConsumers();
  }, [apiUrl]);

  const handleConsumerChange = (e) => {
    const id = e.target.value;
    setSelectedConsumer(id);
    setUserPassword(id); // Prefill password as same as id
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const username = loginMode === 'admin' ? adminUsername : selectedConsumer;
    const password = loginMode === 'admin' ? adminPassword : userPassword;

    if (!username && loginMode === 'user') {
      setError("Por favor, selecciona un departamento de la lista.");
      setLoading(false);
      return;
    }

    try {
      const response = await apiFetch(`${apiUrl}/v1/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Credenciales inválidas');
      }

      const data = await response.json();
      onLogin(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '80vh',
      padding: '20px'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '420px',
        padding: '40px',
        border: '1px solid rgba(139, 92, 246, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-cyan) 100%)',
            width: '60px',
            height: '60px',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px auto',
            boxShadow: 'var(--neon-shadow-purple)'
          }}>
            <Shield size={32} color="#fff" />
          </div>
          <h2 style={{ fontSize: '26px', fontWeight: '800', fontFamily: 'var(--font-heading)' }} className="gradient-text">
            AI FinOps Gateway
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '4px' }}>
            Control de Gobernanza y Costes de IA
          </p>
        </div>

        {/* Selector de Modo de Login */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid var(--glass-border)',
          borderRadius: '8px',
          padding: '4px'
        }}>
          <button
            type="button"
            style={{
              padding: '8px',
              border: 'none',
              background: loginMode === 'user' ? 'rgba(139, 92, 246, 0.15)' : 'transparent',
              color: loginMode === 'user' ? 'var(--accent-purple)' : 'var(--text-secondary)',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
            onClick={() => setLoginMode('user')}
          >
            <Users size={14} />
            Departamento
          </button>
          <button
            type="button"
            style={{
              padding: '8px',
              border: 'none',
              background: loginMode === 'admin' ? 'rgba(217, 70, 239, 0.15)' : 'transparent',
              color: loginMode === 'admin' ? 'var(--accent-pink)' : 'var(--text-secondary)',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 'bold',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s'
            }}
            onClick={() => setLoginMode('admin')}
          >
            <ShieldAlert size={14} />
            Administrador
          </button>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            backgroundColor: 'var(--color-error-bg)',
            border: '1px solid var(--color-error)',
            padding: '12px',
            borderRadius: '10px',
            color: '#fca5a5',
            fontSize: '12px'
          }}>
            <AlertCircle size={18} color="var(--color-error)" style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {loginMode === 'user' ? (
            /* Campos para Modo Departamento (Importados de SQLite) */
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  Selecciona tu Departamento
                </label>
                <select
                  className="select-field"
                  value={selectedConsumer}
                  onChange={handleConsumerChange}
                  required
                  style={{ width: '100%', textTransform: 'capitalize' }}
                >
                  {consumers.length === 0 ? (
                    <option value="">Cargando departamentos...</option>
                  ) : (
                    consumers.map(c => (
                      <option key={c.id} value={c.id}>{c.id}</option>
                    ))
                  )}
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  Contraseña de Acceso
                </label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={userPassword}
                  onChange={(e) => setUserPassword(e.target.value)}
                  required
                />
              </div>
            </>
          ) : (
            /* Campos para Modo Administrador */
            <>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  Usuario Administrador
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="admin"
                  value={adminUsername}
                  onChange={(e) => setAdminUsername(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  Contraseña de Administrador
                </label>
                <input
                  type="password"
                  className="input-field"
                  placeholder="••••••••"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  required
                />
              </div>
            </>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{
              width: '100%',
              justifyContent: 'center',
              marginTop: '10px',
              opacity: loading ? 0.7 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            <Key size={18} />
            {loading ? 'Accediendo...' : 'Ingresar al Portal'}
          </button>
        </form>

        <div style={{
          borderTop: '1px solid var(--glass-border)',
          paddingTop: '16px',
          textAlign: 'center',
          fontSize: '11px',
          color: 'var(--text-muted)'
        }}>
          <p>Los usuarios de departamento se importan en tiempo real de la DB SQLite.</p>
        </div>
      </div>
    </div>
  );
}
