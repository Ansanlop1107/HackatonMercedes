import React from 'react';

export default function FinOpsCharts({ stats, logs }) {
  // Calculate prediction for the next 7 and 30 days
  const calculateForecast = () => {
    if (!stats || !stats.daily_logs || stats.daily_logs.length === 0) {
      return { days7: 0, days30: 0, avgDaily: 0 };
    }

    const uniqueDays = [...new Set(stats.daily_logs.map(log => log.day))];
    const totalSpend = stats.total_spend_usd;
    const numDays = uniqueDays.length || 1;
    const avgDailySpend = totalSpend / numDays;

    return {
      avgDaily: avgDailySpend,
      days7: totalSpend + (avgDailySpend * 7),
      days30: totalSpend + (avgDailySpend * 30)
    };
  };

  const forecast = calculateForecast();

  // Calculate Model Distribution from logs
  const calculateModelDistribution = () => {
    let gpt4oCalls = 0;
    let llama3Calls = 0;
    let cacheHits = 0;
    
    logs.forEach(log => {
      if (log.saved_by_cache === 1) cacheHits++;
      else if (log.model_used === 'gpt-4o' || log.model_used.includes('gpt') || log.model_used.includes('claude')) gpt4oCalls++;
      else if (log.model_used.includes('llama') || log.model_used.includes('mistral')) llama3Calls++;
    });

    const total = logs.length || 1;
    return {
      gpt4o: { count: gpt4oCalls, percentage: (gpt4oCalls / total) * 100 },
      llama3: { count: llama3Calls, percentage: (llama3Calls / total) * 100 },
      cache: { count: cacheHits, percentage: (cacheHits / total) * 100 },
      totalCalls: logs.length
    };
  };

  const dist = calculateModelDistribution();

  // Rendering a simple SVG Line Chart for prediction
  const renderForecastingChart = () => {
    const actualSpend = stats.total_spend_usd;
    const avg = forecast.avgDaily || 0.0;
    
    const days = ['D-5', 'D-4', 'D-3', 'D-2', 'D-1', 'Actual', 'F+2', 'F+4', 'F+6', 'F+7'];
    const points = [
      Math.max(0, actualSpend - avg*5),
      Math.max(0, actualSpend - avg*4),
      Math.max(0, actualSpend - avg*3),
      Math.max(0, actualSpend - avg*2),
      Math.max(0, actualSpend - avg*1),
      actualSpend,
      actualSpend + avg*2,
      actualSpend + avg*4,
      actualSpend + avg*6,
      actualSpend + avg*7
    ];

    const width = 500;
    const height = 180;
    const padding = 30;
    
    const maxVal = Math.max(...points, stats.total_budget_usd) || 10;
    const minVal = 0;
    
    const getCoords = (index, value) => {
      const x = padding + (index * (width - 2 * padding)) / (points.length - 1);
      const y = height - padding - ((value - minVal) * (height - 2 * padding)) / (maxVal - minVal);
      return { x, y };
    };

    let actualPath = '';
    let projectedPath = '';
    
    for (let i = 0; i < points.length; i++) {
      const { x, y } = getCoords(i, points[i]);
      if (i <= 5) {
        if (i === 0) actualPath += `M ${x} ${y}`;
        else actualPath += ` L ${x} ${y}`;
      }
      if (i >= 5) {
        if (i === 5) projectedPath += `M ${x} ${y}`;
        else projectedPath += ` L ${x} ${y}`;
      }
    }

    const budgetCoordsStart = getCoords(0, stats.total_budget_usd);
    const budgetCoordsEnd = getCoords(points.length - 1, stats.total_budget_usd);
    const budgetPath = `M ${budgetCoordsStart.x} ${budgetCoordsStart.y} L ${budgetCoordsEnd.x} ${budgetCoordsEnd.y}`;

    return (
      <div style={{ position: 'relative', width: '100%' }}>
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="var(--text-muted)" opacity={0.3} />
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="var(--text-muted)" opacity={0.1} />
          
          {/* Budget Line */}
          <path d={budgetPath} stroke="var(--color-error)" strokeWidth="1.5" strokeDasharray="4 4" />
          <text x={width - 130} y={budgetCoordsEnd.y - 6} fill="var(--color-error)" fontSize="9" fontWeight="bold">LÍMITE PRESUPUESTO</text>

          {/* Actual Line */}
          <path d={actualPath} fill="none" stroke="var(--accent-purple)" strokeWidth="3" strokeLinecap="round" />
          
          {/* Projected Line */}
          <path d={projectedPath} fill="none" stroke="var(--accent-cyan)" strokeWidth="3" strokeDasharray="5 5" strokeLinecap="round" />

          {/* Circles */}
          {points.map((p, idx) => {
            const { x, y } = getCoords(idx, p);
            return (
              <g key={idx}>
                <circle cx={x} cy={y} r={idx === 5 ? 5 : 3} fill={idx < 5 ? 'var(--accent-purple)' : idx === 5 ? 'var(--accent-pink)' : 'var(--accent-cyan)'} />
                {idx === 5 && <text x={x - 12} y={y - 10} fill="var(--text-primary)" fontSize="9" fontWeight="bold">Hoy</text>}
              </g>
            );
          })}

          {/* X Axis Labels */}
          {days.map((d, idx) => {
            const { x } = getCoords(idx, points[idx]);
            return (
              <text key={idx} x={x} y={height - 8} fill="var(--text-muted)" fontSize="8" textAnchor="middle">
                {d}
              </text>
            );
          })}
        </svg>
      </div>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
      
      {/* Gráfica de Tendencias & Pronóstico */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'var(--font-heading)' }}>
            Tendencias & Análisis Predictivo FinOps
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
            Extrapolación basada en llamadas reales. Tasa de gasto promedio: <strong>${forecast.avgDaily.toFixed(4)} USD / día</strong>.
          </p>
        </div>
        
        {renderForecastingChart()}

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', fontSize: '10px', color: 'var(--text-secondary)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', background: 'var(--accent-purple)', display: 'inline-block' }}></span>
            Historial Gasto
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '3px dashed var(--accent-cyan)', display: 'inline-block' }}></span>
            Predicción (Siguientes 7 días)
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '12px', height: '3px', borderTop: '3px dashed var(--color-error)', display: 'inline-block' }}></span>
            Límite Global
          </span>
        </div>
      </div>

      {/* Distribución de Modelos e Inteligencia FinOps */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700', fontFamily: 'var(--font-heading)' }}>
            Distribución de Modelos & Balance de Carga
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '12px', marginTop: '2px' }}>
            Visualiza qué porcentaje de llamadas ha procesado cada modelo y el ahorro de caché.
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', justifyContent: 'center', flex: 1 }}>
          
          {/* Stacked Progress Bar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
              <span>Carga de Procesamiento</span>
              <span>{dist.totalCalls} llamadas totales</span>
            </div>
            <div style={{ width: '100%', height: '24px', background: 'rgba(255,255,255,0.05)', borderRadius: '6px', overflow: 'hidden', display: 'flex' }}>
              <div style={{ width: `${dist.cache.percentage}%`, background: 'var(--color-success)', height: '100%' }} title={`Cache Hits: ${dist.cache.count}`} />
              <div style={{ width: `${dist.llama3.percentage}%`, background: 'var(--accent-cyan)', height: '100%' }} title={`Llama3/Mistral Económico: ${dist.llama3.count}`} />
              <div style={{ width: `${dist.gpt4o.percentage}%`, background: 'var(--accent-purple)', height: '100%' }} title={`GPT/Claude Premium: ${dist.gpt4o.count}`} />
            </div>
          </div>

          {/* Detalles de la distribución */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
            
            <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <span style={{ fontSize: '11px', color: 'var(--color-success)', fontWeight: 'bold' }}>Cache Hits (SQLite)</span>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>{dist.cache.count}</div>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{dist.cache.percentage.toFixed(0)}% del total</span>
            </div>

            <div style={{ padding: '12px', background: 'rgba(6, 182, 212, 0.05)', border: '1px solid rgba(6, 182, 212, 0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-cyan)', fontWeight: 'bold' }}>Modelos Económicos</span>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>{dist.llama3.count}</div>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{dist.llama3.percentage.toFixed(0)}% del total</span>
            </div>

            <div style={{ padding: '12px', background: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <span style={{ fontSize: '11px', color: 'var(--accent-purple)', fontWeight: 'bold' }}>Modelos Premium</span>
              <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>{dist.gpt4o.count}</div>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{dist.gpt4o.percentage.toFixed(0)}% del total</span>
            </div>

          </div>

          <div style={{
            padding: '12px',
            borderRadius: '8px',
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid var(--glass-border)',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            lineHeight: '1.4'
          }}>
            💡 <strong>Reglas del Enrutador Activas:</strong> El proxy inspecciona la seguridad del prompt, comprueba el estado del presupuesto asignado (economía forzada al 80%) y evalúa el origen/prioridad del departamento antes de enviar la petición al proveedor IA correspondiente.
          </div>

        </div>
      </div>
    </div>
  );
}
