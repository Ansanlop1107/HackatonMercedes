import asyncio
import logging
import os
from typing import Any, Dict

import litellm
from dotenv import load_dotenv

from app.router import MODELS_PROPERTIES

load_dotenv()
logger = logging.getLogger("ai_finops_proxy.llm_clients")

LOCAL_MODEL_APIS = {
    "llama3.2:3b": os.getenv("OLLAMA_PROVIDER_A_URL", "http://localhost:11434"),
    "mistral:7b": os.getenv("OLLAMA_PROVIDER_B_URL", "http://localhost:11435"),
}


async def _mock_cloud_completion(model_name: str, prompt: str) -> Dict[str, Any]:
    """Return a deterministic mock response for cloud models so the demo stays budget-safe."""
    props = MODELS_PROPERTIES.get(model_name, MODELS_PROPERTIES["gpt-5.4-mini"])
    latency_ms = int(props.get("latency_ms", 300))
    prompt_words = len(prompt.split())
    completion_words = 12
    prompt_tokens = int(prompt_words * 1.3)
    completion_tokens = int(completion_words * 1.3)
    total_tokens = prompt_tokens + completion_tokens

    await asyncio.sleep(latency_ms / 1000.0)

    response_text = f"[MOCK-{model_name}] Respuesta simulada para: {prompt[:80]}..."
    cost_per_1k_input = props.get("input_cost", 0.0)
    cost_per_1k_output = props.get("output_cost", 0.0)
    cost_usd = ((prompt_tokens / 1000.0) * cost_per_1k_input) + ((completion_tokens / 1000.0) * cost_per_1k_output)

    return {
        "response": response_text,
        "cost_usd": round(cost_usd, 6),
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
    }


async def _real_cloud_completion(model_name: str, prompt: str):
    """Optional real implementation for future paid-provider usage."""
    provider_prefixes = {
        "gpt-5.4-mini": "openai/",
        "claude-opus-4.7": "anthropic/",
        "llama-3.1-8b-instant": "groq/",
    }
    prefix = provider_prefixes.get(model_name, "")
    messages = [{"role": "user", "content": prompt}]
    return await litellm.acompletion(model=f"{prefix}{model_name}", messages=messages)


async def llamar_proveedor_ia(model_name: str, prompt: str):
    """
    Función unificada que usa Ollama local cuando está disponible y mocks explícitos para cloud.
    """
    if model_name in LOCAL_MODEL_APIS:
        response = await litellm.acompletion(
            model=f"ollama/{model_name}",
            messages=[{"role": "user", "content": prompt}],
            api_base=LOCAL_MODEL_APIS[model_name],
        )
        response_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        coste_usd = response._hidden_params.get("response_cost", 0.0) or 0.0
        return {
            "response": response_content,
            "cost_usd": coste_usd,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        }

    if model_name in {"gpt-5.4-mini", "claude-opus-4.7"} and os.getenv("MOCK_CLOUD_PROVIDERS", "true").lower() == "true":
        logger.info(f"[LLM] Usando mock explícito para el modelo cloud '{model_name}'.")
        return await _mock_cloud_completion(model_name, prompt)

    try:
        response = await _real_cloud_completion(model_name, prompt)
        response_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        coste_usd = response._hidden_params.get("response_cost", 0.0) or 0.0

        return {
            "response": response_content,
            "cost_usd": coste_usd,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        }
    except Exception as e:
        error_msg = f"Error en el proveedor de IA ({type(e).__name__}): {str(e)}. Petición interrumpida."
        logger.error(f"Error crítico en LiteLLM: {error_msg}")
        return {
            "response": error_msg,
            "cost_usd": 0.0,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }