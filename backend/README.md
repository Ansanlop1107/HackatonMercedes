# ⚙️ AI FinOps Proxy — Backend Setup & Guide

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square)
![LiteLLM](https://img.shields.io/badge/LiteLLM-1E90FF?style=flat-square)

El backend de **AI FinOps Proxy** es un motor de gobernanza e intermediación de llamadas construido en **FastAPI** (Python). Implementa la seguridad DLP contra inyecciones y fugas, caché semántica, un motor de reglas para enrutamiento (Decision Router) y auditoría financiera automática mediante **SQLite 3**.

---

## 🛠️ Prerrequisitos

Asegúrate de tener instalados:
- **Docker Desktop** (en Windows, configurado con WSL2).
- **Python 3.10+** instalado en tu sistema.

---

## 🚀 Pasos de Instalación y Arranque

Sigue estos 5 pasos ordenados para poner en marcha el backend:

### 1. Iniciar los Proveedores de IA Locales (Docker)
El backend utiliza contenedores locales de **Ollama** para procesar peticiones con datos sensibles o bajo presupuesto sin incurrir en costes externos:
- **Proveedor A:** Corriendo en `http://localhost:11434` (modelo Llama 3.2:3b).
- **Proveedor B:** Corriendo en `http://localhost:11435` (modelo Mistral:7b).

Para levantarlos, abre tu terminal desde la raíz de la carpeta `backend/` y ejecuta:
```bash
docker compose up -d
```
*(Puedes verificar que estén corriendo con `docker ps`).*

---

### 2. Configurar el Entorno Virtual de Python
Es altamente recomendable aislar las dependencias utilizando un entorno virtual. Ejecuta en la terminal del backend:

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**En macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Instalar Dependencias
Una vez activado el entorno virtual (`.venv`), instala los paquetes necesarios de Python:
```bash
pip install fastapi uvicorn litellm python-dotenv pandas
```

---

### 4. Configurar las Claves API (`.env`)
LiteLLM requiere de claves de API de los proveedores cloud para enrutar los modelos externos. Crea un archivo llamado `.env` en la carpeta `backend/` (`backend/.env`) e ingresa tus credenciales según corresponda:

```ini
# --- CLAVES API CLOUD ---
# Groq (Obligatorio para simular el enrutamiento económico Llama3.1)
GROQ_API_KEY=gsk_tu_clave_de_groq_aqui

# OpenAI (Opcional - para modelos GPT)
OPENAI_API_KEY=sk-proj-tu_clave_de_openai_aqui

# Anthropic (Opcional - para modelos Claude)
ANTHROPIC_API_KEY=sk-ant-tu_clave_de_anthropic_aqui

# Google Gemini (Opcional)
GEMINI_API_KEY=tu_clave_de_gemini_aqui

# --- CONFIGURACIÓN DE OLLAMA LOCAL ---
OLLAMA_PROVIDER_A_URL=http://localhost:11434
OLLAMA_PROVIDER_B_URL=http://localhost:11435
```

---

### 5. Iniciar la API de FastAPI
Con el entorno virtual activo y el archivo `.env` configurado, arranca el servidor web ASGI ejecutando:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Una vez levantada, la API del proxy estará disponible en:
- 🚀 **Servidor Local:** [http://localhost:8000](http://localhost:8000)
- 📖 **Documentación Interactiva (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Control de Salud (Health):** [http://localhost:8000/health](http://localhost:8000/health)

---

## 🛡️ Endpoints del Proxy FinOps

La API expone los siguientes endpoints esenciales:

- **`POST /v1/chat/completions`**: Endpoint proxy compatible con el formato estándar de OpenAI. Intercepta la llamada, analiza seguridad/DLP, ejecuta caché/enrutamiento y procesa con LiteLLM.
- **`POST /v1/admin/login`**: Inicio de sesión del panel de administración.
- **`GET /v1/admin/stats`**: Calcula métricas globales, ahorro agregado de caché y la regresión lineal para la predicción de consumo de presupuestos.
- **`GET /v1/admin/consumers`**: Devuelve la lista de departamentos activos y su gasto.
- **`POST /v1/admin/consumers`**: Crea un nuevo departamento o equipo asignando presupuesto.
- **`PUT /v1/admin/consumers/{id}/budget`**: Actualiza el límite presupuestario asignado.
- **`GET /v1/admin/logs`**: Historial completo de auditoría de transacciones del proxy.

---

## 🛠️ Diagnóstico y Detalle de Errores

En caso de fallo en el proveedor LLM (como claves incorrectas, fallos de red o errores de conexión con Ollama), el backend intercepta el error y devuelve un mensaje detallado que indica el tipo de excepción y la descripción del error. Esto facilita la resolución de problemas directamente desde la consola de desarrollo del frontend sin necesidad de examinar logs internos de Docker.
