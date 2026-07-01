import React, { useState } from 'react';
import { 
  Edit2, Check, PlusCircle, Database, Trash2, ShieldAlert 
} from 'lucide-react';

export default function BudgetManager({ 
  user, stats, adminMessage, setAdminMessage, actionLoading, 
  onUpdateBudget, onCreateDept, onResetDatabase 
}) {
  const [editingDept, setEditingDept] = useState(null);
  const [newBudget, setNewBudget] = useState('');
  const [newDeptId, setNewDeptId] = useState('');
  const [newDeptBudget, setNewDeptBudget] = useState('');

  const handleUpdateClick = (dept) => {
    setEditingDept(dept.id);
    setNewBudget(dept.budget.toString());
  };

  const handleSaveBudget = async (deptId) => {
    if (!newBudget || isNaN(newBudget)) return;
    const success = await onUpdateBudget(deptId, parseFloat(newBudget));
    if (success) {
      setEditingDept(null);
      setNewBudget('');
    }
  };

  const handleSubmitCreate = async (e) => {
    e.preventDefault();
    if (!newDeptId || !newDeptBudget || isNaN(newDeptBudget)) return;
    const success = await onCreateDept(newDeptId.trim().toLowerCase(), parseFloat(newDeptBudget));
    if (success) {
      setNewDeptId('');
      setNewDeptBudget('');
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '24px' }}>
      
      {/* Presupuestos de Departamentos */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'var(--font-heading)' }}>
            Consumos Departamentales & Configuración de Cuotas
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
            Monitorea el gasto acumulado de cada equipo y define sus límites mensuales.
          </p>
        </div>

        {adminMessage && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '13px',
            backgroundColor: adminMessage.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            border: '1px solid ' + (adminMessage.type === 'success' ? 'var(--color-success)' : 'var(--color-error)'),
            color: adminMessage.type === 'success' ? '#a7f3d0' : '#fca5a5'
          }}>
            {adminMessage.text}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {stats.departments.map(dept => {
            const spendPercentage = Math.min(100, (dept.current_spend / (dept.budget || 1)) * 100);
            const isOverBudget = dept.current_spend >= dept.budget;
            
            return (
              <div key={dept.id} style={{
                padding: '14px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.01)',
                border: '1px solid var(--glass-border)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong style={{ fontSize: '14px', textTransform: 'capitalize', color: 'var(--text-primary)' }}>{dept.id}</strong>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Gasto: ${dept.current_spend.toFixed(4)} USD / €{(dept.current_spend * 0.92).toFixed(4)} EUR
                    </div>
                  </div>

                  {user.role === 'admin' ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {editingDept === dept.id ? (
                        <>
                          <input
                            type="number"
                            className="input-field"
                            style={{ width: '80px', padding: '6px 10px', fontSize: '13px' }}
                            value={newBudget}
                            onChange={(e) => setNewBudget(e.target.value)}
                            placeholder="Límite"
                          />
                          <button
                            onClick={() => handleSaveBudget(dept.id)}
                            disabled={actionLoading}
                            style={{
                              background: 'var(--color-success)', border: 'none', borderRadius: '6px',
                              width: '28px', height: '28px', display: 'flex', alignItems: 'center',
                              justifyContent: 'center', cursor: 'pointer'
                            }}
                          >
                            <Check size={14} color="#fff" />
                          </button>
                        </>
                      ) : (
                        <>
                          <span style={{ fontSize: '13px', fontWeight: 'bold' }}>Límite: ${dept.budget.toFixed(2)}</span>
                          <button
                            onClick={() => handleUpdateClick(dept)}
                            style={{
                              background: 'transparent', border: '1px solid var(--glass-border)', borderRadius: '6px',
                              width: '26px', height: '26px', display: 'flex', alignItems: 'center',
                              justifyContent: 'center', cursor: 'pointer'
                            }}
                            className="btn-secondary"
                          >
                            <Edit2 size={12} />
                          </button>
                        </>
                      )}
                    </div>
                  ) : (
                    <span style={{ fontSize: '13px', fontWeight: 'bold' }}>Límite: ${dept.budget.toFixed(2)}</span>
                  )}
                </div>

                {/* Progress bar */}
                <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${spendPercentage}%`,
                    height: '100%',
                    background: isOverBudget 
                      ? 'linear-gradient(90deg, #ef4444 0%, #b91c1c 100%)' 
                      : spendPercentage > 85 
                        ? 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)'
                        : 'linear-gradient(90deg, var(--accent-purple) 0%, var(--accent-cyan) 100%)',
                    borderRadius: '4px',
                    transition: 'width 0.4s ease-out'
                  }}></div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Formulario Crear Departamento */}
        {user.role === 'admin' && (
          <form onSubmit={handleSubmitCreate} style={{
            display: 'flex',
            gap: '10px',
            paddingTop: '16px',
            borderTop: '1px solid var(--glass-border)',
            alignItems: 'end'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
              <label style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>ID Departamento</label>
              <input
                type="text"
                className="input-field"
                style={{ padding: '8px 12px', fontSize: '13px' }}
                placeholder="ej: equipo-ventas"
                value={newDeptId}
                onChange={(e) => setNewDeptId(e.target.value)}
                required
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '90px' }}>
              <label style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>Presupuesto ($)</label>
              <input
                type="number"
                className="input-field"
                style={{ padding: '8px 12px', fontSize: '13px' }}
                placeholder="10"
                value={newDeptBudget}
                onChange={(e) => setNewDeptBudget(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={actionLoading} className="btn-primary" style={{ padding: '9px 12px', fontSize: '12px', display: 'flex', gap: '6px' }}>
              <PlusCircle size={15} />
              Agregar
            </button>
          </form>
        )}
      </div>

      {/* Acciones de Base de Datos y Herramientas */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '700', fontFamily: 'var(--font-heading)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Database size={18} color="var(--accent-purple)" />
            Control de Base de Datos
          </h3>
          
          <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: '1.4' }}>
            Permite reiniciar los contadores a cero y vaciar el historial de logs de la base de datos de SQLite para iniciar pruebas desde limpio.
          </p>

          {user.role === 'admin' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              
              <button 
                onClick={onResetDatabase} 
                disabled={actionLoading}
                className="btn-secondary" 
                style={{ 
                  justifyContent: 'center', 
                  fontSize: '13px', 
                  borderColor: 'rgba(239,68,68,0.3)',
                  color: '#fca5a5',
                  background: 'rgba(239,68,68,0.05)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <Trash2 size={14} />
                Reiniciar Base de Datos (Limpieza a 0)
              </button>

            </div>
          ) : (
            <div style={{ 
              padding: '12px', 
              borderRadius: '8px', 
              background: 'rgba(245,158,11,0.05)', 
              border: '1px solid rgba(245,158,11,0.2)',
              fontSize: '11px',
              color: '#fcd34d',
              display: 'flex',
              gap: '8px',
              alignItems: 'center'
            }}>
              <ShieldAlert size={16} />
              <span>Solo el administrador puede borrar los consumos acumulados.</span>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
