import os
import logging
import litellm
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("ai_finops_proxy.llm_clients")

LOCAL_MODEL_APIS = {
    "llama3.2:3b": os.getenv("OLLAMA_PROVIDER_A_URL", "http://localhost:11434"),
    "mistral:7b": os.getenv("OLLAMA_PROVIDER_B_URL", "http://localhost:11435"),
}


async def llamar_proveedor_ia(model_name: str, prompt: str):
    """
    Función unificada con LiteLLM que intermedia con cualquier modelo
    y calcula de forma nativa los costes de FinOps.
    """
    messages = [{"role": "user", "content": prompt}]
    
    try:
        # 1. ENRUTAMIENTO LOCAL (Vuestro Docker con Ollama)
        if model_name in LOCAL_MODEL_APIS:
            response = await litellm.acompletion(
                model=f"ollama/{model_name}",
                messages=messages,
                api_base=LOCAL_MODEL_APIS[model_name],
            )
        
        # 2. ENRUTAMIENTO CLOUD (Groq, OpenAI, Mistral API, etc.)
        else:
            # LiteLLM detecta el proveedor por el prefijo (ej: "groq/llama3-8b-8192")
            # Requiere que tengáis la API Key en el archivo .env (ej: GROQ_API_KEY)
            response = await litellm.acompletion(
                model=model_name,
                messages=messages
            )
        
        # 3. EXTRACCIÓN DE MÉTRICAS FINOPS
        response_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # LiteLLM calcula el coste en USD usando su base de datos interna de precios.
        # Para Ollama (local) devolverá automáticamente 0.0, ¡lo cual es perfecto para FinOps!
        coste_usd = response._hidden_params.get("response_cost", 0.0) or 0.0

        return {
            "response": response_content,
            "cost_usd": coste_usd,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }

    except Exception as e:
        error_msg = f"Error en el proveedor de IA ({type(e).__name__}): {str(e)}. Petición interrumpida."
        logger.error(f"Error crítico en LiteLLM: {error_msg}")
        return {
            "response": error_msg,
            "cost_usd": 0.0,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }