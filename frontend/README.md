# 💻 AI FinOps Portal — Frontend Setup & Guide

![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![Lucide](https://img.shields.io/badge/Lucide_Icons-FF4081?style=flat-square)

Este es el portal web de administración y simulación interactiva de **AI FinOps Proxy**, construido utilizando **React 19** y **Vite 8** para garantizar una experiencia fluida, reactiva y moderna.

---

## 🎨 Características del Diseño

- **Modo Oscuro e Interfaz Premium:** Diseñado con técnicas modernas de `CSS Glassmorphism`, transparencias sutiles y efectos interactivos.
- **AI Playground:** Consola tipo chat donde los desarrolladores simulan llamadas de sus aplicaciones, visualizando en tiempo real la decisión del proxy, el coste estimado (en USD y Euros), el ahorro y los tokens.
- **Admin Dashboard:** Vista ejecutiva con KPIs financieros (Gasto global, Ahorro total acumulado), barras de presupuesto por departamento y edición directa de cuotas.
- **Gráfica de Predicción SVG:** Un análisis de regresión lineal simple que proyecta el gasto del departamento a futuro para predecir cuándo agotarán el saldo.
- **Auditoría e Historial (Audit Trail):** Registro visual de solicitudes previas con filtros avanzados por departamento, tipo de modelo (económico vs premium) y estado de caché.

---

## 🛠️ Prerrequisitos

- Tener instalado **Node.js 18+** y **npm** (gestor de paquetes).

---

## 🚀 Guía de Arranque Rápido

Sigue estos pasos para arrancar el frontend en tu máquina local:

### 1. Entrar en la carpeta del frontend
Abre tu terminal y dirígete al directorio `frontend`:
```bash
cd frontend
```

### 2. Instalar dependencias de Node.js
Ejecuta el siguiente comando para instalar las dependencias necesarias:
```bash
npm install
```

### 3. Configurar la URL del API Backend
Abre el archivo [App.jsx](file:///d:/HackatonFinal/frontend/src/App.jsx) en tu editor. Ubica la constante `API_URL` en las primeras líneas del archivo y configúrala para que apunte a tu proxy local o a la URL pública generada por ngrok:

```javascript
// Para desarrollo en local directo:
const API_URL = 'http://localhost:8000';

// O si expones tu backend con ngrok para testing remoto:
const API_URL = 'https://tu-subdominio.ngrok-free.dev';
```

*(Nota: La comunicación del frontend ya incluye automáticamente la cabecera `ngrok-skip-browser-warning` para saltarse pantallas intermedias de ngrok).*

### 4. Arrancar el servidor de desarrollo
Lanza el servidor local en modo de desarrollo ejecutando:
```bash
npm run dev
```

### 5. Acceder a la aplicación
Abre tu navegador de internet y dirígete a:
👉 [**http://localhost:5173**](http://localhost:5173)

---

## 🔑 Credenciales para Pruebas

Para simular distintos flujos y comportamientos en el dashboard y el playground, puedes usar los siguientes perfiles de inicio de sesión:

- **Rol de Administrador (FinOps Admin):**
  - **Usuario:** `admin`
  - **Contraseña:** `admin`
  - *(Permite: Modificar presupuestos en tiempo real, crear consumidores y ver logs globales).*
- **Rol de Departamento (Usuario Normal):**
  - **Usuario:** Nombre o ID de un departamento registrado (ej: `equipo-marketing`, `mercedes-drive-assistant`, `mercedes-lab-experiments`).
  - **Contraseña:** El mismo valor que el nombre del usuario.
  - *(Permite: Interactuar con el Playground, ver el presupuesto restante de su equipo y su predicción de gasto individual).*

---

## 🏗️ Comprobación y Compilación de Producción

Para validar el empaquetado del frontend o generar el código de distribución estático listo para producción, ejecuta:
```bash
npm run build
```
Esto creará una carpeta optimizada `dist/` en la raíz de `frontend/` conteniendo los bundles listos para cualquier servidor web estático.
