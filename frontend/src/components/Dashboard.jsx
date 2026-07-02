import React, { useState, useEffect } from 'react';
import { 
  DollarSign, Landmark, PiggyBank, TrendingUp, RefreshCw, ShieldAlert 
} from 'lucide-react';
import FinOpsCharts from './FinOpsCharts';
import BudgetManager from './BudgetManager';
import AuditLogsTable from './AuditLogsTable';
import { apiFetch } from '../services/apiFetch';

export default function Dashboard({ user, apiUrl }) {
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [adminMessage, setAdminMessage] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch Stats
      const statsRes = await apiFetch(`${apiUrl}/v1/admin/stats`);
      if (!statsRes.ok) throw new Error('Error al cargar estadísticas.');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch Logs (load up to 10000 logs for client-side filtering)
      const logsRes = await apiFetch(`${apiUrl}/v1/admin/logs?limit=10000`);
      if (!logsRes.ok) throw new Error('Error al cargar logs.');
      const logsData = await logsRes.json();
      setLogs(logsData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleUpdateBudget = async (deptId, budgetAmount) => {
    if (!budgetAmount || isNaN(budgetAmount)) return false;
    try {
      setActionLoading(true);
      const response = await apiFetch(`${apiUrl}/v1/admin/consumers/${deptId}/budget`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ budget: parseFloat(budgetAmount) })
      });

      if (!response.ok) throw new Error('No se pudo actualizar el presupuesto.');
      
      setAdminMessage({ type: 'success', text: `Presupuesto de '${deptId}' actualizado a $${parseFloat(budgetAmount).toFixed(2)}.` });
      fetchDashboardData();
      return true;
    } catch (err) {
      setAdminMessage({ type: 'error', text: err.message });
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateDept = async (deptId, budgetAmount) => {
    if (!deptId || !budgetAmount || isNaN(budgetAmount)) return false;

    try {
      setActionLoading(true);
      const response = await apiFetch(`${apiUrl}/v1/admin/consumers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: deptId.trim().toLowerCase(),
          budget: parseFloat(budgetAmount)
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error creando departamento.');
      }

      setAdminMessage({ type: 'success', text: `Departamento '${deptId}' registrado correctamente.` });
      fetchDashboardData();
      return true;
    } catch (err) {
      setAdminMessage({ type: 'error', text: err.message });
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const handleResetDatabase = async () => {
    if (!window.confirm("¿Estás seguro de reiniciar todos los gastos a cero y vaciar el historial de logs?")) return;
    
    try {
      setActionLoading(true);
      const response = await apiFetch(`${apiUrl}/v1/admin/reset`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Error al reiniciar base de datos.');
      
      setAdminMessage({ type: 'success', text: "Base de datos restablecida correctamente. Todos los consumos vuelven a $0.00." });
      fetchDashboardData();
    } catch (err) {
      setAdminMessage({ type: 'error', text: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', color: 'var(--accent-purple)' }}>
        <RefreshCw size={40} className="animate-spin" style={{ animationDuration: '2s', marginBottom: '16px' }} />
        <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Cargando analíticas FinOps...</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>Conectando con la base de datos de SQLite y calculando predicciones...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel" style={{ padding: '40px', margin: '20px', textAlign: 'center', borderColor: 'var(--color-error)' }}>
        <ShieldAlert size={48} color="var(--color-error)" style={{ marginBottom: '16px' }} />
        <h3 style={{ fontSize: '20px', color: 'var(--text-primary)' }}>Error en la Pasarela de Administración</h3>
        <p style={{ color: 'var(--text-secondary)', marginTop: '8px', fontSize: '14px' }}>{error}</p>
        <p style={{ color: 'var(--text-muted)', marginTop: '4px', fontSize: '12px' }}>Asegúrate de que el servidor proxy (FastAPI) está encendido en el puerto 8000.</p>
        <button className="btn-primary" onClick={fetchDashboardData} style={{ marginTop: '20px' }}>Reintentar Conexión</button>
      </div>
    );
  }

  // Calculate prediction for the next 30 days for the global KPI
  const calculateForecast = () => {
    if (!stats || !stats.daily_logs || stats.daily_logs.length === 0) {
      return { days30: 0 };
    }

    const uniqueDays = [...new Set(stats.daily_logs.map(log => log.day))];
    const totalSpend = stats.total_spend_usd;
    const numDays = uniqueDays.length || 1;
    const avgDailySpend = totalSpend / numDays;

    return {
      days30: totalSpend + (avgDailySpend * 30)
    };
  };

  const forecast = calculateForecast();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', margin: '20px' }} className="animate-fade-in">
      
      {/* 1. KPIs principales */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        
        {/* KPI: Gasto Actual */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'rgba(139, 92, 246, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <DollarSign size={24} color="var(--accent-purple)" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Gasto Actual Acumulado</div>
            <div style={{ fontSize: '22px', fontWeight: '800' }}>${stats.total_spend_usd.toFixed(2)}</div>
            <div style={{ fontSize: '11px', color: 'var(--accent-cyan)', fontWeight: '600' }}>
              €{stats.total_spend_eur.toFixed(2)} EUR
            </div>
          </div>
        </div>

        {/* KPI: Presupuesto Global */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'rgba(6, 182, 212, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Landmark size={24} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Límite Presupuestario Global</div>
            <div style={{ fontSize: '22px', fontWeight: '800' }}>${stats.total_budget_usd.toFixed(2)}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              €{stats.total_budget_eur.toFixed(2)} EUR
            </div>
          </div>
        </div>

        {/* KPI: Ahorro por Caché */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'rgba(16, 185, 129, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <PiggyBank size={24} color="var(--color-success)" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Ahorro FinOps (Caché)</div>
            <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--color-success)' }}>
              +${stats.saved_cost_usd.toFixed(4)}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {stats.cache_hits} hits ({stats.total_calls > 0 ? ((stats.cache_hits / stats.total_calls) * 100).toFixed(0) : 0}%)
            </div>
          </div>
        </div>

        {/* KPI: Proyección 30 días */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px', backgroundColor: 'rgba(217, 70, 239, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <TrendingUp size={24} color="var(--accent-pink)" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Previsión Fin de Mes (30d)</div>
            <div style={{ fontSize: '22px', fontWeight: '800', color: forecast.days30 > stats.total_budget_usd ? 'var(--color-error)' : 'var(--text-primary)' }}>
              ${forecast.days30.toFixed(2)}
            </div>
            <div style={{ fontSize: '11px', color: forecast.days30 > stats.total_budget_usd ? 'var(--color-error)' : 'var(--color-success)' }}>
              {forecast.days30 > stats.total_budget_usd ? 'Excede presupuesto global' : 'Dentro del presupuesto'}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Sección Gráficas e Distribuciones */}
      <FinOpsCharts stats={stats} logs={logs} />

      {/* 3. Sección Admin Control y Gestión de Presupuestos */}
      <BudgetManager 
        user={user} 
        stats={stats} 
        adminMessage={adminMessage} 
        setAdminMessage={setAdminMessage} 
        actionLoading={actionLoading} 
        onUpdateBudget={handleUpdateBudget} 
        onCreateDept={handleCreateDept} 
        onResetDatabase={handleResetDatabase} 
      />

      {/* 4. Tabla de Auditoría Avanzada con Filtros */}
      <AuditLogsTable logs={logs} stats={stats} />

    </div>
  );
}
