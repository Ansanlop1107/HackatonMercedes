# AI FinOps Gateway - Guia de Arranque (Backend + Frontend)

Este workspace contiene dos proyectos separados dentro del mismo repositorio:

- `backend/`: API proxy FinOps construida con FastAPI.
- `frontend/`: portal web construido con React + Vite.

La idea es ejecutar ambos de forma local y exponer el backend con ngrok para que el frontend consuma una URL publica HTTPS.

---

## 1) Arquitectura rapida

1. El backend corre en local (puerto `8000`) y ofrece endpoints como:
	 - `POST /v1/chat/completions`
	 - `POST /v1/admin/login`
	 - `GET /v1/admin/stats`
2. ngrok publica ese backend local en una URL HTTPS.
3. El frontend usa esa URL de ngrok como `API_URL`.

---

## 2) Prerrequisitos

Instala estas herramientas antes de empezar:

- Docker Desktop (con WSL2 en Windows).
- Python 3.10+.
- Node.js 18+ y npm.
- ngrok (cuenta gratuita).

Opcional (recomendado para pruebas del starter):

- Task (`task`) y jq.

---

## 3) Levantar proveedores LLM locales (Docker)

El backend enruta modelos locales usando URLs por defecto:

- Provider A: `http://localhost:11434`
- Provider B: `http://localhost:11435`

Desde la carpeta `backend`:

```powershell
cd backend
docker compose up -d
```

Verifica que los contenedores estan activos:

```powershell
docker ps
```

Si es la primera vez con Ollama, puede tardar por descarga de imagen/modelos.

---

## 4) Arrancar el backend (FastAPI)

### 4.1 Crear y activar entorno virtual (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4.2 Instalar dependencias Python

En este repo no hay `requirements.txt`, asi que instalalas manualmente:

```powershell
pip install fastapi uvicorn litellm python-dotenv pandas
```

### 4.3 Ejecutar API

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Comprobaciones:

- Health: `http://localhost:8000/health`
- Swagger: `http://localhost:8000/docs`

---

## 5) Exponer el backend con ngrok

En otra terminal (manteniendo el backend encendido):

```powershell
ngrok http 8000
```

ngrok te mostrara una URL publica, por ejemplo:

`https://tu-subdominio.ngrok-free.dev`

Esa sera la base URL del proxy para el frontend.

---

## 6) Conectar frontend con el proxy (ngrok)

Abre `frontend/src/App.jsx` y actualiza la constante `API_URL` con la URL HTTPS de ngrok.

Ejemplo:

```jsx
const API_URL = 'https://tu-subdominio.ngrok-free.dev';
```

Nota:

- El frontend ya incluye la cabecera `ngrok-skip-browser-warning: true` en `frontend/src/services/apiFetch.js`, por lo que no debes hacer ajustes adicionales para ese warning.

---

## 7) Arrancar el frontend (React + Vite)

Desde la carpeta `frontend`:

```powershell
cd frontend
npm install
npm run dev
```

Abre:

- `http://localhost:5173`

---

## 8) Flujo recomendado de arranque (orden)

1. Levantar Docker providers (`backend/docker-compose.yml`).
2. Levantar FastAPI en `localhost:8000`.
3. Levantar ngrok apuntando a `8000`.
4. Pegar URL de ngrok en `frontend/src/App.jsx`.
5. Levantar frontend con Vite.

---

## 9) Credenciales y uso rapido

Login administrador:

- usuario: `admin`
- password: `admin`

Login de departamento:

- usuario: id del departamento existente (ej. `equipo-marketing`)
- password: mismo valor que el usuario

---

## 10) Troubleshooting

### Error de conexion en frontend

- Revisa que `API_URL` en `frontend/src/App.jsx` sea exactamente la URL activa de ngrok.
- Si reiniciaste ngrok, su URL cambia: actualiza `API_URL` y recarga frontend.

### El backend no responde en `:8000`

- Verifica que el entorno virtual este activo.
- Revisa logs de uvicorn en la terminal del backend.

### Conflicto de puertos 11434/11435

- Cierra otros servicios Ollama locales o cambia puertos en `backend/docker-compose.yml`.

### CORS / bloqueo navegador

- Este backend tiene CORS abierto (`allow_origins=["*"]`).
- Si aparece warning de ngrok, el frontend ya envia `ngrok-skip-browser-warning`.

---

## 11) Estructura del monorepo

```text
HackatonFinal/
	backend/    # Proxy FastAPI + SQLite + reglas FinOps
	frontend/   # Portal React/Vite (dashboard, playground, login)
```

