# 🚀 AI FinOps Proxy — Smart Gateway para Gobernanza de IA

> **La capa de control y optimización de costes definitiva para empresas que consumen IA Generativa.**

## 📖 Visión General

A medida que el uso de LLMs crece en las empresas, también lo hacen los costes ocultos, el "vendor lock-in" y los riesgos de seguridad. **AI FinOps Proxy** es un API Gateway inteligente (Reverse Proxy) que se interpone entre los usuarios internos y múltiples proveedores de IA (OpenAI, Anthropic, Groq, Ollama). 

Su misión es clara: **Interceptar, Proteger, Enrutar inteligentemente y Auditar** cada petición para maximizar el ahorro, garantizar la disponibilidad y proteger los datos sensibles.

---

## 🏗️ Arquitectura de Alto Nivel

El sistema se divide en tres componentes principales:

1. **Frontend Enriquecido (Cliente):** Envía prompts acompañados de un contexto rico (archivos, metadatos, requisitos de latencia o formato de salida).
2. **Core Proxy (Smart Router):** Un pipeline de 6 capas basado en el patrón *Chain of Responsibility* que toma decisiones milisegundo a milisegundo.
3. **FinOps Admin Dashboard:** Panel de control en tiempo real para visualizar consumo, ahorro (Total Savings), bloqueos de seguridad y predicciones de agotamiento de presupuesto.

---

## 🧠 Pipeline de Orquestación (El "Cerebro" del Proxy)

Cada solicitud enviada por un usuario pasa por un **flujo estricto de 6 fases** antes de llegar a cualquier modelo.

### 1. Capa de Seguridad y Cumplimiento (Security & PII Shield)
* **Anti-Prompt Injection:** Bloquea intentos de manipulación del *system prompt* usando heurísticas de seguridad.
* **Prevención de Fuga de Datos (DLP):** Escanea el contenido en busca de PII (Tarjetas de crédito, DNI, Emails). Si detecta datos sensibles, marca la petición para ser procesada **exclusivamente por modelos locales** (ej. Ollama), garantizando la privacidad y el cumplimiento del GDPR.

### 2. Capa de Caché Semántica
* Comprueba si la misma petición (o una semánticamente idéntica) ya fue procesada recientemente.
* **Impacto:** Respuestas instantáneas con coste `$0.00`. El ahorro se suma a la métrica global de *Total Savings*.

### 3. Gatekeeper FinOps (Control de Presupuesto)
* Verifica la identidad del consumidor (`team_id` o `consumer_id`).
* Evalúa si el equipo tiene saldo suficiente para la petición. Si el presupuesto se ha agotado, la petición se bloquea en la puerta (HTTP 403), previniendo sorpresas en la factura.

### 4. Motor de Enrutamiento Multidimensional (Smart Routing)
El núcleo del proyecto. En lugar de enviar todo al modelo más caro, el sistema evalúa múltiples dimensiones de la solicitud y elige el modelo óptimo basándose en un árbol de decisión:

| Dimensión Analizada | Regla de Enrutamiento | Proveedor/Modelo Destino |
| :--- | :--- | :--- |
| **Privacidad (PII)** | Si el prompt contiene datos sensibles. | 🔒 **Ollama (Modelo Local)** |
| **Modalidad** | Si el usuario adjunta imágenes. | 👁️ **Modelo de Visión** (GPT-4o / Claude) |
| **Análisis de Datos** | Si el usuario adjunta archivos CSV/Excel. | 📊 **Code Interpreter / Analítico** |
| **Tamaño del Contexto** | Si el prompt + archivos supera los 8k tokens. | 📚 **Modelo Long-Context Eficiente** (Haiku / Flash) |
| **Formato Estricto** | Si el usuario requiere salida en JSON. | ⚙️ **Especializado en JSON** (Llama 3 / GPT-4o-mini) |
| **Urgencia / Latencia** | Si se requiere respuesta en tiempo real. | ⚡ **LPU Fast Engine** (Groq) |
| **Complejidad (NLP)** | Tareas lógicas (Código, matemáticas, refactorización). | 🧠 **Premium** (GPT-4o / Claude 3.5) |
| **Simplicidad (NLP)** | Tareas básicas (Resumen, traducción, chat). | 💰 **Económico** (Groq / Llama 8b) |

### 5. Resiliencia y Fallback (Alta Disponibilidad)
* Si el proveedor seleccionado sufre una caída, devuelve un timeout o un error 5xx, el proxy hace un *retry* automático hacia el **segundo mejor modelo** calculado, garantizando que el usuario siempre reciba respuesta sin interrupciones.

### 6. FinOps Tracking y Auditoría
* Una vez obtenida la respuesta, el proxy extrae el uso exacto de `prompt_tokens` y `completion_tokens`.
* Calcula el coste real utilizando tarifas actualizadas.
* Registra en la base de datos el **Motivo de Enrutamiento** ("Routing Reason") y calcula el **Ahorro Generado** frente a haber usado un modelo premium por defecto.

---

## 📊 Dashboard de Administración y Análisis predictivo

La interfaz de administración proporciona visibilidad total a nivel C-Level (CTO / CFO):

* **Gráfica Predictiva (Regresión Lineal):** Analiza la tendencia de gasto de cada departamento y predice en qué fecha exacta se quedarán sin presupuesto si continúan a ese ritmo.
* **Métrica Estrella - Total Savings:** Un contador en tiempo real que demuestra el ROI del proxy, mostrando el dinero ahorrado gracias a la caché y al enrutamiento eficiente a modelos más baratos.
* **Audit Trail & Alertas:** Registro de todos los bloqueos por seguridad (Prompt Injection), re-enrutamientos por privacidad (PII) y peticiones denegadas por límite de presupuesto.

---

## 🛠️ Stack Tecnológico

*(Nota: Sustituye esto con las tecnologías reales de tu proyecto)*
* **Frontend:** React y Bite
* **Backend Proxy:** Python (FastAPI)
* **Base de Datos:** SQLite
* **Proveedores IA Integrados:** Ollama (Local), Groq, OpenAI, Anthropic

---

## 💡 Criterios de Evaluación del Hackathon Cumplidos

- [x] **Multi-proveedor:** Orquesta llamadas entre APIs en la nube y modelos locales.
- [x] **Consumidores Múltiples:** Trackea departamentos aislados de forma independiente.
- [x] **Visibilidad de Costes:** Cálculo granular de tokens y desglose de precio por usuario.
- [x] **Gobernanza:** Límites de presupuesto estrictos con respuesta visible de bloqueo.
- [x] **Decisión Inteligente:** Motor basado en reglas explícitas demostrando trade-offs lógicos entre coste, calidad, velocidad y privacidad.
