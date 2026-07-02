# 🚀 AI FinOps Proxy — Smart Gateway para Gobernanza de IA

> *La capa de control y optimización de costes definitiva para empresas que consumen IA Generativa.*

---

## 📖 Visión General

A medida que el uso de LLMs crece en las empresas, también lo hacen los costes ocultos, el "vendor lock-in" y los riesgos de seguridad. **AI FinOps Proxy** es un API Gateway inteligente (Reverse Proxy) que se interpone entre los usuarios internos y múltiples proveedores de IA (OpenAI, Anthropic, Groq, Ollama). 

Su misión es clara: **Interceptar, Proteger, Enrutar inteligentemente y Auditar** cada petición para maximizar el ahorro, garantizar la disponibilidad y proteger los datos sensibles.

---

## 🛠️ Tecnologías Utilizadas

### Capas del Sistema

```text
┌────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND PORTAL                           │
│  [ React 19 ]   [ Vite 8 ]   [ Lucide Icons ]   [ CSS Glassmorphism ]  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ HTTP / HTTPS (ngrok)
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                             BACKEND ENGINE                             │
│       [ Python 3.10+ ]   [ FastAPI ]   [ Uvicorn ]   [ LiteLLM ]       │
└───────────┬───────────────────────┬───────────────────────┬────────────┘
            │                       │                       │
┌───────────▼───────────┐ ┌─────────▼───────────┐ ┌─────────▼───────────┐
│     DATABASE LAYER    │ │    LOCAL PROVIDERS  │ │    CLOUD PROVIDERS  │
│      [ SQLite 3 ]     │ │   [ Ollama (Docker) ] │ │  [ Groq, OpenAI,  │
│   (Logs & Budgets)    │ │(Llama 3.2 & Mistral)│ │   Anthropic, etc. ] │
└───────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

### Stack Tecnológico (Badges)

- **Frontend:**  
  ![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
  ![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
  ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
  ![Lucide](https://img.shields.io/badge/Lucide_Icons-FF4081?style=flat-square)  
  *Portal web con interfaz premium reactiva, panel translúcido (`CSS Glassmorphism`) y modo oscuro.*

- **Backend & Proxy Core:**  
  ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
  ![Uvicorn](https://img.shields.io/badge/Uvicorn-222222?style=flat-square)
  ![LiteLLM](https://img.shields.io/badge/LiteLLM-1E90FF?style=flat-square)  
  *Motor del proxy API de alto rendimiento con enrutador unificado asíncrono.*

- **Base de Datos & Seguridad:**  
  ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)  
  *Base de datos persistente SQLite 3 para control de presupuestos, auditoría histórica (logs) y caché semántica. DLP mediante expresiones regulares.*

- **Modelos locales (Docker):**  
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
  ![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square)  
  *Contenedores Docker para levantar instancias locales de Ollama con Llama3.2:3b y Mistral:7b.*

---

## 🏗️ Arquitectura de Alto Nivel

El sistema se divide en tres componentes principales:

1. **Frontend Enriquecido (Cliente):** Envía prompts acompañados de un contexto de consumidor y metadatos financieros.
2. **Core Proxy (Smart Router):** Un pipeline de 6 capas basado en el patrón *Chain of Responsibility* que toma decisiones en tiempo real sobre cada llamada de IA.
3. **FinOps Admin Dashboard:** Panel de control en tiempo real para visualizar consumo, ahorro (*Total Savings*), bloqueos de seguridad y predicciones de agotamiento de presupuesto.

---

## 🧠 Pipeline de Orquestación (El "Cerebro" del Proxy)

Cada solicitud enviada por un usuario pasa por un **flujo estricto de 6 fases** antes de llegar a cualquier modelo.

### 1. Capa de Seguridad y Cumplimiento (Security & PII Shield)
- **Anti-Prompt Injection:** Bloquea intentos de manipulación del system prompt mediante heurísticas de seguridad en la entrada.
- **Prevención de Fuga de Datos (DLP):** Escanea el contenido del prompt buscando información personalmente identificable o PII (tarjetas de crédito, DNI, emails, matrículas, bastidores VIN, teléfonos, IPs privadas). Si detecta datos sensibles, marca la petición para ser procesada **exclusivamente por modelos locales** (ej. Ollama), garantizando la privacidad y el cumplimiento regulatorio (GDPR/DLP).

### 2. Capa de Caché Semántica
- Comprueba si la misma petición (o una idéntica) ha sido procesada recientemente.
- **Impacto:** Si hay coincidencia (Cache Hit), devuelve la respuesta almacenada inmediatamente con coste $0.00 y latencia mínima. El ahorro generado se suma a la métrica global de *Total Savings*.

### 3. Gatekeeper FinOps (Control de Presupuesto)
- Verifica la identidad del consumidor (`X-Consumer-ID`).
- Evalúa si el departamento o equipo tiene saldo suficiente en la base de datos de SQLite. Si el presupuesto se ha agotado, la petición se bloquea de inmediato (HTTP 429), previniendo sobrecostes no autorizados.

### 4. Motor de Enrutamiento Multidimensional (Smart Routing)
El núcleo inteligente del proxy. Evalúa múltiples dimensiones de la solicitud y elige el modelo óptimo basándose en las siguientes reglas del enrutador:

| Dimensión Analizada | Criterio / Regla de Enrutamiento | Proveedor/Modelo Destino |
| :--- | :--- | :--- |
| **Privacidad (PII)** | Si el prompt contiene datos sensibles detectados por DLP. | 🔒 **Ollama (Modelo Local Llama 3.2)** |
| **Presupuesto Agotado > 80%** | Si el consumo del departamento supera el 80% de su límite asignado. | 💰 **Ollama Local (Economía Forzada)** |
| **Prioridad Experimental** | Si el consumidor pertenece al departamento de laboratorios / experimentos. | 💰 **Ollama Local (Bajo Coste)** |
| **Uso Normal (Standard)** | Consumidor estándar, prompt limpio y presupuesto holgado. | ⚡ **gpt-5.4-mini (Estándar)** |
| **Uso Premium (Pro)** | Consumidor pro, prompt extenso y presupuesto más ajustado. | ⚡ **claude-opus-4.7 (Pro)** |

### 5. Resiliencia y Fallback (Alta Disponibilidad)
- Si el proveedor seleccionado sufre una caída de red o devuelve un error 5xx, el proxy realiza un reintento automático (retry) redirigiendo la petición hacia el **segundo mejor modelo** local o cloud, garantizando que el usuario siempre reciba respuesta.

### 6. FinOps Tracking y Auditoría
- Tras obtener la respuesta, el proxy extrae el uso exacto de tokens de entrada (`prompt_tokens`) y salida (`completion_tokens`).
- Calcula el coste real de la llamada según tarifas del proveedor y actualiza el gasto del departamento.
- Registra en SQLite el log histórico detallado indicando las reglas aplicadas en el enrutamiento y el ahorro generado.

---

## 📊 Dashboard de Administración y Análisis predictivo

La interfaz de administración proporciona visibilidad total C-Level:

- **Métrica Estrella - Total Savings:** Un contador en tiempo real que demuestra el ROI del proxy, acumulando el coste ahorrado gracias al uso de la caché semántica y al desvío inteligente hacia modelos locales más baratos.
- **Proyección de Consumo:** Analiza la tendencia media diaria de gasto de cada departamento y proyecta cuánto presupuesto quedará disponible en los próximos días si se mantiene el mismo ritmo de consumo.
- **Audit Trail & Alertas:** Tabla interactiva que registra todos los bloqueos por seguridad (Prompt Injection), desvíos por privacidad (PII) y peticiones bloqueadas por presupuesto superado.

---

## 📂 Estructura del Repositorio

El monorepo está dividido en dos grandes carpetas:

- [**`backend/`**](file:///d:/HackatonFinal/backend): Código del servidor FastAPI, configuración de la base de datos SQLite (`app/finops.db`), el Decision Router y el cliente LiteLLM.
- [**`frontend/`**](file:///d:/HackatonFinal/frontend): Interfaz gráfica modular construida en React + Vite.

Para ver las guías paso a paso de instalación y arranque para cada componente, por favor accede a sus respectivos archivos README:

1. ⚙️ **Instalación del Servidor:** [**Guía de Instalación del Backend (FastAPI)**](file:///d:/HackatonFinal/backend/README.md)
2. 💻 **Instalación del Cliente:** [**Guía de Instalación del Frontend (React)**](file:///d:/HackatonFinal/frontend/README.md)
