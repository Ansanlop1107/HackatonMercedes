import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.admin import router as admin_router

# Configurar el registro de logs para visibilidad global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ai_finops_proxy")

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="AI FinOps Proxy",
    description="Middleware de gestión y optimización de costes para APIs de IA Gen e Inteligencia Artificial.",
    version="0.1.0"
)

# Configurar CORS para permitir peticiones
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Incluir las rutas del módulo chat (/v1/chat/completions)
app.include_router(chat_router)
# Incluir las rutas de administración (/v1/admin)
app.include_router(admin_router)

@app.get("/health", tags=["General"])
async def health_check():
    """
    Endpoint simple para verificar la salud del proxy.
    """
    return {"status": "healthy", "service": "AI FinOps Proxy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8080, reload=True)