import React, { useState, useEffect } from 'react';
import { Send, CheckCircle, AlertTriangle, AlertOctagon, RefreshCw, Zap, Server, Coins, ShieldAlert } from 'lucide-react';
import { apiFetch } from '../services/apiFetch';

export default function Playground({ user, apiUrl }) {
  const [prompt, setPrompt] = useState('');
  const [selectedConsumer, setSelectedConsumer] = useState(
    user.role === 'admin' ? '' : user.username
  );
  
  const [loading, setLoading] = useState(false);
  const [consumers, setConsumers] = useState([]);
  
  // Results states
  const [responseStatus, setResponseStatus] = useState(null);
  const [responseData, setResponseData] = useState(null);
  const [errorDetails, setErrorDetails] = useState(null);
  const [modelUsed, setModelUsed] = useState(null);
  const [costUsd, setCostUsd] = useState(0);
  const [tokens, setTokens] = useState(null);
  
  // Real routing headers returned by API
  const [routingReason, setRoutingReason] = useState('');
  const [actionsApplied, setActionsApplied] = useState('');
  const [securityRestriction, setSecurityRestriction] = useState('');
  const [sensitiveDataFound, setSensitiveDataFound] = useState('');

  const fetchConsumers = async () => {
    try {
      const response = await apiFetch(`${apiUrl}/v1/admin/consumers`);
      if (response.ok) {
        const data = await response.json();
        setConsumers(data);
        if (user.role === 'admin' && data.length > 0 && !selectedConsumer) {
          setSelectedConsumer(data[0].id);
        }
      }
    } catch (err) {
      console.error('Error fetching consumers:', err);
    }
  };

  useEffect(() => {
    fetchConsumers();
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();
    if (user.role === 'admin') return; // Guard: admin cannot make requests
    if (!prompt.trim()) return;

    setLoading(true);
    setResponseStatus(null);
    setResponseData(null);
    setErrorDetails(null);
    setModelUsed(null);
    setCostUsd(0);
    setTokens(null);
    setRoutingReason('');
    setActionsApplied('');
    setSecurityRestriction('');
    setSensitiveDataFound('');

    const headers = {
      'Content-Type': 'application/json',
      'X-Consumer-ID': selectedConsumer
    };

    try {
      const response = await apiFetch(`${apiUrl}/v1/chat/completions`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          prompt: prompt
        })
      });

      setResponseStatus(response.status);

      // Read custom FinOps headers
      const xModel = response.headers.get("X-Model-Selected");
      const xActions = response.headers.get("X-Actions-Applied") || "none";
      const xRestriction = response.headers.get("X-Routing-Restriction") || "delegate_to_finops";
      const xSensitive = response.headers.get("X-Sensitive-Data-Detected") || "none";

      setActionsApplied(xActions);
      setSecurityRestriction(xRestriction);
      setSensitiveDataFound(xSensitive);

      if (!response.ok) {
        const errData = await response.json();
        setErrorDetails(errData.detail || 'Error desconocido');
        
        if (response.status === 403) {
          setRoutingReason('Gobernanza FinOps (403): El ID del departamento no está registrado en SQLite.');
        } else if (response.status === 429) {
          setRoutingReason('Gobernanza FinOps (429): Límite de presupuesto excedido para este departamento.');
        } else if (response.status === 400) {
          setRoutingReason(`Error (400): ${errData.detail || 'Petición inválida.'}`);
        } else {
          setRoutingReason('Error al procesar la solicitud en el proxy.');
        }
        return;
      }

      const data = await response.json();
      setResponseData(data.choices[0].message.content);
      const finalModel = data.model;
      setModelUsed(finalModel);
      setTokens(data.usage);

      // Calculate cost
      const isCached = data.id.includes('cache') || xActions.includes('cache_hit') || data.usage.prompt_tokens === 0;
      
      // Select description based on real actions header
      let explanation = '';
      if (xActions.includes('cache_hit')) {
        setCostUsd(0);
        explanation = 'Cache Hit: El prompt exacto fue consultado recientemente. Se retorna la respuesta en caché a coste cero.';
      } else {
        // Calculate cost based on model used
        let inCost = 0.00075;
        let outCost = 0.0045;
        if (finalModel.includes('opus')) { inCost = 0.005; outCost = 0.025; }
        else if (finalModel.includes('instant')) { inCost = 0.00005; outCost = 0.00008; }
        else if (finalModel.includes('3b')) { inCost = 0.00006; outCost = 0.00006; }
        else if (finalModel.includes('7b')) { inCost = 0.00024; outCost = 0.00024; }

        const cost = ((data.usage.prompt_tokens / 1000.0) * inCost) + ((data.usage.completion_tokens / 1000.0) * outCost);
        setCostUsd(cost);

        // Build explanation string
        const reasons = [];
        if (xRestriction === 'force_local') {
          reasons.push(`Seguridad (DLP): Detectados datos sensibles (${xSensitive}). Se forzó enrutamiento local a ${finalModel}.`);
        }
        if (xActions.includes('activate_savings_mode')) {
          reasons.push('Límite del 80%: Presupuesto departamental casi agotado. Forzado modelo económico Llama3.');
        }
        if (xActions.includes('force_low_cost_model')) {
          reasons.push('Prioridad Experimental: Departamento con recursos limitados. Forzado Llama3.');
        }
        if (xActions.includes('degrade_model')) {
          reasons.push('Sin Justificación: Claude Opus degradado a GPT-5.4-mini por falta de cabecera X-Justification.');
        }
        if (xActions.includes('reroute_cost_threshold')) {
          reasons.push('Límite de Coste: Coste superaba $0.10. Re-enrutado a modelo más barato.');
        }
        if (reasons.length === 0) {
          reasons.push(`Enrutamiento Exitoso: Ejecutado en '${finalModel}' de forma óptima.`);
        }
        explanation = reasons.join(' | ');
      }
      setRoutingReason(explanation);

    } catch (err) {
      setResponseStatus(500);
      setErrorDetails(err.message || 'Error de conexión');
      setRoutingReason('Error de red al conectar con el servidor de la pasarela.');
    } finally {
      setLoading(false);
      fetchConsumers();
    }
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 380px',
      gap: '24px',
      margin: '20px',
      alignItems: 'start'
    }} className="animate-fade-in">
      
      {/* Columna Principal - Chat / Consola */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', minHeight: '600px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '700', fontFamily: 'var(--font-heading)' }}>
            AI Playground & Test Console
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Simula llamadas de tus aplicaciones al proxy FinOps y analiza el comportamiento de la gobernanza en tiempo real.
          </p>
        </div>

        {user.role === 'admin' ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '60px 40px',
            background: 'rgba(239, 68, 68, 0.03)',
            border: '1px solid rgba(239, 68, 68, 0.15)',
            borderRadius: '16px',
            color: '#fca5a5',
            textAlign: 'center',
            gap: '16px',
            margin: 'auto 0'
          }}>
            <ShieldAlert size={56} color="var(--color-error)" />
            <h3 style={{ fontSize: '18px', fontWeight: '800', fontFamily: 'var(--font-heading)' }}>
              Acceso Restringido al Administrador
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '440px', lineHeight: '1.6' }}>
              El usuario administrador **no tiene permitido** realizar peticiones a la pasarela de IA para evitar el consumo inapropiado de cuotas.
            </p>
          </div>
        ) : (
          /* Formulario de Entrada de prompts para Usuarios Normales */
          <>
            {/* Consumidor Activo */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              padding: '16px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--glass-border)'
            }}>
              <label style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                Consumidor Activo (X-Consumer-ID)
              </label>
              <input
                type="text"
                className="input-field"
                value={user.username}
                disabled
                style={{ opacity: 0.8, background: 'rgba(255,255,255,0.02)', fontWeight: 'bold', textTransform: 'capitalize' }}
              />
            </div>

            {/* Formulario Prompt */}
            <form onSubmit={handleSend} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: '500' }}>
                  Mensaje del Usuario (Prompt)
                </label>
                <textarea
                  className="input-field"
                  style={{
                    minHeight: '120px',
                    resize: 'vertical',
                    fontFamily: 'var(--font-body)',
                    lineHeight: '1.5'
                  }}
                  placeholder="Introduce tu pregunta. Ej: 'Hola mundo' o incluye información de tarjetas para activar DLP local."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  required
                />
              </div>

              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
                style={{
                  alignSelf: 'end',
                  opacity: loading ? 0.7 : 1,
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? <RefreshCw size={16} className="animate-spin" /> : <Send size={16} />}
                {loading ? 'Procesando...' : 'Enviar Solicitud'}
              </button>
            </form>

            {/* Consola de Respuesta */}
            <div style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              gap: '10px',
              marginTop: '10px'
            }}>
              <h3 style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: '600' }}>
                Respuesta de la IA / Salida del Proxy
              </h3>

              <div style={{
                flex: 1,
                background: 'rgba(0, 0, 0, 0.25)',
                border: '1px solid var(--glass-border)',
                borderRadius: '12px',
                padding: '20px',
                fontFamily: 'monospace',
                fontSize: '14px',
                lineHeight: '1.6',
                color: responseData ? 'var(--text-primary)' : 'var(--text-muted)',
                whiteSpace: 'pre-wrap',
                minHeight: '160px',
                overflowY: 'auto'
              }}>
                {loading ? (
                  <span style={{ color: 'var(--accent-purple)' }}>Enrutando la petición...</span>
                ) : responseData ? (
                  responseData
                ) : errorDetails ? (
                  <span style={{ color: 'var(--color-error)' }}>[ERROR]: {errorDetails}</span>
                ) : (
                  'Esperando prompt...'
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Columna Lateral - Widgets de Diagnóstico */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Widget 1: HTTP Status Code */}
        <div className="glass-panel" style={{
          padding: '20px',
          borderLeft: '4px solid ' + (
            responseStatus === 200 ? 'var(--color-success)' :
            responseStatus === 403 ? 'var(--color-error)' :
            responseStatus === 429 ? 'var(--color-warning)' :
            'var(--glass-border)'
          )
        }}>
          <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '10px' }}>
            Estado de la Petición (HTTP)
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {responseStatus === 200 && <CheckCircle size={28} color="var(--color-success)" />}
            {responseStatus === 429 && <AlertTriangle size={28} color="var(--color-warning)" />}
            {responseStatus === 403 && <AlertOctagon size={28} color="var(--color-error)" />}
            {!responseStatus && <Server size={28} color="var(--text-muted)" />}

            <div>
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {responseStatus ? `Status: ${responseStatus}` : 'Inactivo'}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {responseStatus === 200 && '200 OK — Solicitud Autorizada'}
                {responseStatus === 429 && '429 Quota Exceeded — Límite de Gasto'}
                {responseStatus === 403 && '403 Forbidden — No Autorizado'}
                {!responseStatus && 'Ninguna petición realizada en la sesión.'}
              </div>
            </div>
          </div>
        </div>

        {/* Widget 2: Enrutamiento y Modelo */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '10px' }}>
            Decisión del Enrutamiento Real
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <Zap size={24} color={actionsApplied.includes('cache_hit') ? 'var(--accent-cyan)' : 'var(--accent-purple)'} />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                {actionsApplied.includes('cache_hit') ? 'Caché Interna (Hit)' : modelUsed ? modelUsed : 'Sin Enrutar'}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {actionsApplied.includes('cache_hit') ? 'Respuesta servida desde SQLite' : 'Modelo LLM enrutado'}
              </div>
            </div>
          </div>
          {routingReason && (
            <div style={{
              fontSize: '12px',
              padding: '10px',
              borderRadius: '8px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid var(--glass-border)',
              lineHeight: '1.4',
              color: 'var(--text-secondary)'
            }}>
              <strong>Reglas Evaluadas:</strong>
              <div style={{ marginTop: '4px' }}>{routingReason}</div>
              <div style={{ marginTop: '6px', fontSize: '10px', color: 'var(--text-muted)' }}>
                Acciones API: <code>{actionsApplied}</code> | Seguridad: <code>{securityRestriction}</code>
              </div>
            </div>
          )}
        </div>

        {/* Widget 3: Costes y Conversión a Euros */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '10px' }}>
            Cómputo Financiero
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Coste Estimado USD</span>
              <span style={{ fontSize: '16px', fontWeight: 'bold', color: 'var(--accent-purple)' }}>
                ${costUsd.toFixed(6)}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--glass-border)', paddingBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Cambio a Euros (€)</span>
              <span style={{ fontSize: '16px', fontWeight: 'bold', color: 'var(--accent-pink)' }}>
                €{(costUsd * 0.92).toFixed(6)}
              </span>
            </div>

            {tokens && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Tokens Entrada:</span>
                  <span>{tokens.prompt_tokens}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Tokens Salida:</span>
                  <span>{tokens.completion_tokens}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: '600' }}>
                  <span>Tokens Totales:</span>
                  <span>{tokens.total_tokens}</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Widget 4: Tips de Ahorro FinOps */}
        <div className="glass-panel" style={{ padding: '20px', background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%)' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '8px' }}>
            Políticas de Optimización
          </h3>
          <ul style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '6px', paddingLeft: '14px' }}>
            <li><strong>WHO (Prioridad):</strong> mercedes-drive-assistant es 'crítico', experimentos es 'experimental' (baja prioridad).</li>
            <li><strong>WHEN (Ahorro):</strong> Si el gasto del departamento supera el 80%, se le fuerza a Llama3 local.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
