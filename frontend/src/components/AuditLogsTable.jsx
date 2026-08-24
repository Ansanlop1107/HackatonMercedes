import React, { useState } from 'react';
import { FileText, Search } from 'lucide-react';

export default function AuditLogsTable({ 
  logsData, 
  stats, 
  logsLoading,
  logsPage,
  setLogsPage,
  logsLimit,
  setLogsLimit,
  searchPrompt,
  onSearchChange,
  filterModel,
  onModelFilterChange,
  filterCache,
  onCacheFilterChange,
  filterDept,
  onDeptFilterChange
}) {
  const logs = logsData.items || [];
  const total = logsData.total || 0;
  const pages = logsData.pages || 1;

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileText size={20} color="var(--accent-purple)" />
          <h3 style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'var(--font-heading)' }}>
            Registro de Auditoría & Historial
          </h3>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          {logsLoading ? 'Cargando...' : `Mostrando ${logs.length} de ${total} transacciones`}
        </span>
      </div>

      {/* Filtros de la Tabla */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1.5fr 1fr 1fr 1fr', 
        gap: '12px',
        padding: '16px',
        borderRadius: '12px',
        background: 'rgba(255,255,255,0.02)',
        border: '1px solid var(--glass-border)'
      }}>
        
        {/* Búsqueda */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Buscar en Prompt</label>
          <div style={{ position: 'relative' }}>
            <input
              type="text"
              className="input-field"
              style={{ padding: '8px 12px 8px 32px', fontSize: '13px' }}
              placeholder="Ej: consulta, análisis..."
              value={searchPrompt}
              onChange={(e) => onSearchChange(e.target.value)}
            />
            <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '12px' }} />
          </div>
        </div>

        {/* Filtro Modelo */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Filtrar por Tarifa</label>
          <select 
            className="select-field" 
            style={{ padding: '8px 12px', fontSize: '13px' }}
            value={filterModel}
            onChange={(e) => onModelFilterChange(e.target.value)}
          >
            <option value="all">Todos los modelos</option>
            <option value="economy">Modelos Económicos (Llama3/Mistral)</option>
            <option value="premium">Modelos Premium (GPT/Claude)</option>
          </select>
        </div>

        {/* Filtro Caché */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Filtrar por Caché</label>
          <select 
            className="select-field" 
            style={{ padding: '8px 12px', fontSize: '13px' }}
            value={filterCache}
            onChange={(e) => onCacheFilterChange(e.target.value)}
          >
            <option value="all">Todos los estados</option>
            <option value="hit">Cache HIT (ahorro)</option>
            <option value="miss">Cache MISS (consulta real)</option>
          </select>
        </div>

        {/* Filtro Departamento */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <label style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Filtrar por Equipo</label>
          <select 
            className="select-field" 
            style={{ padding: '8px 12px', fontSize: '13px' }}
            value={filterDept}
            onChange={(e) => onDeptFilterChange(e.target.value)}
          >
            <option value="all">Todos los equipos</option>
            {stats && stats.departments && stats.departments.map(d => (
              <option key={d.id} value={d.id}>{d.id}</option>
            ))}
          </select>
        </div>

      </div>

      {/* Tabla */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--text-secondary)' }}>
              <th style={{ padding: '12px 8px' }}>Fecha y Hora</th>
              <th style={{ padding: '12px 8px' }}>Departamento</th>
              <th style={{ padding: '12px 8px' }}>Prompt</th>
              <th style={{ padding: '12px 8px' }}>Modelo Usado</th>
              <th style={{ padding: '12px 8px' }}>Coste (USD)</th>
              <th style={{ padding: '12px 8px' }}>Ahorro (USD)</th>
              <th style={{ padding: '12px 8px' }}>Motivo de Enrutado</th>
              <th style={{ padding: '12px 8px' }}>Estado</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.2s' }}>
                <td style={{ padding: '12px 8px', color: 'var(--text-muted)' }}>{log.timestamp}</td>
                <td style={{ padding: '12px 8px', fontWeight: 'bold' }}>{log.consumer_id}</td>
                <td style={{ padding: '12px 8px', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={log.prompt}>
                  {log.prompt}
                </td>
                <td style={{ padding: '12px 8px' }}>
                  <span style={{
                    padding: '3px 8px', borderRadius: '12px', fontSize: '10px',
                    background: log.saved_by_cache ? 'rgba(16, 185, 129, 0.15)' : (log.model_used.includes('gpt') || log.model_used.includes('claude')) ? 'rgba(139, 92, 246, 0.15)' : 'rgba(6, 182, 212, 0.15)',
                    color: log.saved_by_cache ? 'var(--color-success)' : (log.model_used.includes('gpt') || log.model_used.includes('claude')) ? 'var(--accent-purple)' : 'var(--accent-cyan)',
                    border: '1px solid ' + (log.saved_by_cache ? 'rgba(16, 185, 129, 0.3)' : (log.model_used.includes('gpt') || log.model_used.includes('claude')) ? 'rgba(139, 92, 246, 0.3)' : 'rgba(6, 182, 212, 0.3)')
                  }}>
                    {log.model_used}
                  </span>
                </td>
                <td style={{ padding: '12px 8px', fontWeight: 'bold', color: log.saved_by_cache ? 'var(--color-success)' : 'var(--text-primary)' }}>
                  ${log.cost.toFixed(6)}
                </td>
                <td style={{ padding: '12px 8px', fontWeight: 'bold', color: 'var(--color-success)' }}>
                  ${log.savings ? log.savings.toFixed(6) : '0.000000'}
                </td>
                <td style={{ padding: '12px 8px', maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-muted)' }} title={log.routing_reason || 'N/A'}>
                  {log.routing_reason || 'N/A'}
                </td>
                <td style={{ padding: '12px 8px' }}>
                  {log.event_type === 'blocked_security' || log.event_type === 'blocked_budget' ? (
                    <span style={{ color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px' }}>
                      {log.event_type === 'blocked_security' ? 'BLOQUEADO' : 'PRESUPUESTO'}
                    </span>
                  ) : log.saved_by_cache ? (
                    <span style={{ color: 'var(--color-success)', background: 'var(--color-success-bg)', padding: '2px 6px', borderRadius: '4px', fontSize: '11px' }}>
                      HIT
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>MISS</span>
                  )}
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No se encontraron transacciones. El sistema está limpio y listo para registrar nuevos consumos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid var(--glass-border)',
        flexWrap: 'wrap',
        gap: '12px',
        fontSize: '13px'
      }}>
        {/* Selector de límite por página */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Mostrar</span>
          <select
            className="select-field"
            style={{ padding: '4px 8px', fontSize: '12px', width: '70px', background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)' }}
            value={logsLimit}
            onChange={(e) => {
              setLogsLimit(parseInt(e.target.value));
              setLogsPage(1);
            }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span style={{ color: 'var(--text-secondary)' }}>registros</span>
        </div>

        {/* Botones de navegación de página */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            className="btn-secondary"
            style={{ padding: '5px 10px', fontSize: '12px', minWidth: 'auto' }}
            onClick={() => setLogsPage(1)}
            disabled={logsPage === 1 || logsLoading}
          >
            « Primero
          </button>
          <button
            className="btn-secondary"
            style={{ padding: '5px 10px', fontSize: '12px', minWidth: 'auto' }}
            onClick={() => setLogsPage(prev => Math.max(1, prev - 1))}
            disabled={logsPage === 1 || logsLoading}
          >
            ‹ Anterior
          </button>
          
          <span style={{ color: 'var(--text-primary)', padding: '0 8px', fontWeight: '600' }}>
            Página {logsPage} de {pages}
          </span>

          <button
            className="btn-secondary"
            style={{ padding: '5px 10px', fontSize: '12px', minWidth: 'auto' }}
            onClick={() => setLogsPage(prev => Math.min(pages, prev + 1))}
            disabled={logsPage === pages || logsLoading}
          >
            Siguiente ›
          </button>
          <button
            className="btn-secondary"
            style={{ padding: '5px 10px', fontSize: '12px', minWidth: 'auto' }}
            onClick={() => setLogsPage(pages)}
            disabled={logsPage === pages || logsLoading}
          >
            Último »
          </button>
        </div>
      </div>

    </div>
  );
}
