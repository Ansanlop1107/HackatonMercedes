import logging
import re
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.db import get_db_connection, init_db
from app.llm_clients import llamar_proveedor_ia
from app.router import DecisionRouter
from app.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseUsage,
    Message,
)
from app.security import SecurityLayer

# Configurar logger para este módulo específico de FinOps
logger = logging.getLogger("ai_finops_proxy.api.chat")

# Declarar el APIRouter con el prefijo /v1 exigido por el Frontend
router = APIRouter(prefix="/v1")

# Listado básico de Stopwords en Español e Inglés para el Caché Semántico
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "y", "o", "a", "en", "para", "por", 
    "con", "que", "es", "son", "se", "lo", "como", "mas", "pero", "para", "por", "si", "no", "mi", "su", 
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "of", "is", "are", "it", 
    "this", "that", "you", "me", "my", "your", "he", "she", "they", "we"
}

def calcular_similitud_jaccard(text1: str, text2: str) -> float:
    """
    Calcula el coeficiente de similitud de Jaccard entre dos textos normalizados,
    omitiendo puntuaciones y stopwords comunes.
    """
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    
    words1 = words1 - STOPWORDS
    words2 = words2 - STOPWORDS
    
    if not words1 or not words2:
        return 0.0
        
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union


def _build_response(model_name: str, response_text: str, usage_data: dict, request_id: str) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=request_id,
        object="chat.completion",
        created=int(datetime.now(timezone.utc).timestamp()),
        model=model_name,
        choices=[
            ChatCompletionResponseChoice(
                index=0,
                message=Message(role="assistant", content=response_text),
                finish_reason="stop",
            )
        ],
        usage=ChatCompletionResponseUsage(**usage_data),
    )


def _set_response_header(response: Response, header_name: str, value: str) -> None:
    """Set a response header using an ASCII-safe fallback for non-ASCII characters."""
    safe_value = value.encode("ascii", "replace").decode("ascii")
    response.headers[header_name] = safe_value


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    response: Response,
    x_consumer_id: str = Header(..., alias="X-Consumer-ID", description="Identificador único del consumidor del servicio"),
    x_justification: Optional[str] = Header(None, alias="X-Justification", description="Justificación requerida para modelos premium o prompts de gran tamaño"),
):
    """
    Endpoint principal que intercepta las llamadas tipo OpenAI.
    Aplica Gobernanza (Presupuestos), Seguridad (Anti-Injection/DLP),
    Caché de costes y delega la ejecución de IA de forma transparente en LiteLLM.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        init_db()

        cursor.execute(
            "SELECT budget, current_spend FROM consumers WHERE id = ?",
            (x_consumer_id,),
        )
        consumer = cursor.fetchone()

        if not consumer:
            logger.warning(f"[PROXY] Consumidor '{x_consumer_id}' intentó acceder pero no está registrado.")
            cursor.execute(
                "INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason, event_type) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0.0, ?, ?)",
                (x_consumer_id, user_prompt if 'user_prompt' in locals() else '', 'Consumidor no autorizado', 'blocked', 0.0, 'Consumidor no registrado', 'blocked_budget'),
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Consumidor '{x_consumer_id}' no registrado o no autorizado en el sistema de Mercedes.",
            )

        budget = float(consumer["budget"])
        current_spend = float(consumer["current_spend"])

        user_prompt = ""
        if request.prompt:
            user_prompt = request.prompt
        elif request.messages:
            user_messages = [msg.content for msg in request.messages if msg.role == "user"]
            if user_messages:
                user_prompt = user_messages[-1]
            else:
                user_prompt = request.messages[-1].content
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar un campo 'prompt' o una lista estructurada de 'messages'.",
            )

        # Escanear tanto el prompt como el contenido del archivo adjunto para máxima seguridad (PII/DLP)
        scan_text = user_prompt
        if request.file_content:
            scan_text += "\n" + request.file_content
        routing_restriction, detected_types = SecurityLayer.evaluate_security(scan_text)

        logger.info(
            f"[PROXY] Consumidor: {x_consumer_id} | Presupuesto: ${budget:.2f} | Gasto Actual: ${current_spend:.6f}"
        )
        if current_spend >= budget:
            logger.warning(
                f"[PROXY] Consumidor '{x_consumer_id}' excedió su presupuesto (${current_spend:.6f}/${budget:.2f}). Petición bloqueada."
            )
            cursor.execute(
                "INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason, event_type) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0.0, ?, ?)",
                (x_consumer_id, user_prompt, 'Presupuesto excedido', 'blocked', 0.0, 'Presupuesto excedido', 'blocked_budget'),
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Presupuesto excedido. Solicite una ampliación de crédito FinOps.",
            )

        requested_model = request.model or "gpt-5.4-mini"
        final_model, final_prompt, applied_actions, routing_reason = DecisionRouter.evaluate_rules(
            consumer_id=x_consumer_id,
            prompt=user_prompt,
            requested_model=requested_model,
            current_spend=current_spend,
            budget=budget,
            has_justification=bool(x_justification),
            routing_restriction=routing_restriction,
            file_name=request.file_name,
            file_type=request.file_type,
            file_size=request.file_size,
            file_content=request.file_content,
            require_json=request.require_json,
            urgency=request.urgency
        )

        # --- Capa 3: Gatekeeper FinOps (Control de Presupuesto con Estimación) ---
        from app.router import MODELS_PROPERTIES
        props = MODELS_PROPERTIES.get(final_model, MODELS_PROPERTIES["gpt-5.4-mini"])
        
        words_prompt = len(final_prompt.split())
        file_words = len(request.file_content.split()) if request.file_content else 0
        est_input_tokens = int((words_prompt + file_words) * 1.3)
        est_output_tokens = 500  # Baseline estimado de salida
        
        est_cost = ((est_input_tokens / 1000.0) * props["input_cost"]) + ((est_output_tokens / 1000.0) * props["output_cost"])
        
        if current_spend >= budget or current_spend + est_cost >= budget:
            logger.warning(
                f"[PROXY] Presupuesto superado con la estimación de la llamada. Gasto actual: ${current_spend:.6f} | Est. Petición: ${est_cost:.6f} | Límite: ${budget:.2f}"
            )
            cursor.execute(
                "INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason, event_type) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0.0, ?, ?)",
                (x_consumer_id, user_prompt, 'Estimación de costo supera presupuesto', 'blocked', 0.0, 'Estimación de coste supera el presupuesto', 'blocked_budget'),
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Gobernanza FinOps: La estimación de coste de esta petición (${est_cost:.4f}) superaría tu límite presupuestario mensual."
            )

        # 2. Capa de Caché Semántica (Jaccard Similarity)
        cached_response = None
        cached_model = None
        
        cursor.execute(
            """
            SELECT prompt, response, model_used FROM logs
            WHERE response IS NOT NULL AND saved_by_cache = 0
              AND timestamp >= datetime('now', '-24 hours')
            ORDER BY timestamp DESC LIMIT 100
            """
        )
        recent_logs = cursor.fetchall()
        
        best_sim = 0.0
        best_match = None
        
        for r in recent_logs:
            # Si se exige modelo local, el registro de caché también debe ser local
            if routing_restriction == "force_local" and r["model_used"] not in ["llama3.2:3b", "mistral:7b"]:
                continue
            sim = calcular_similitud_jaccard(user_prompt, r["prompt"])
            if sim > best_sim:
                best_sim = sim
                best_match = r
                
        # Si la similitud supera el 80%, consideramos un Semantic Cache Hit!
        if best_sim >= 0.80 and best_match:
            cached_response = best_match["response"]
            cached_model = best_match["model_used"]
            logger.info(f"[CACHE] Semantic Cache Hit! Similitud: {best_sim:.2f} con prompt: '{best_match['prompt']}'")

        if cached_response is not None:
            final_model = cached_model or final_model
            
            # Estimar tokens del cache hit para calcular el ahorro
            words_prompt = len(user_prompt.split())
            file_words = len(request.file_content.split()) if request.file_content else 0
            est_p_tokens = int((words_prompt + file_words) * 1.3)
            est_c_tokens = int(len(cached_response.split()) * 1.3)
            premium_est_cost = ((est_p_tokens / 1000.0) * 0.005) + ((est_c_tokens / 1000.0) * 0.025)
            savings = premium_est_cost
            
            cursor.execute(
                """
                INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """,
                (x_consumer_id, user_prompt, cached_response, final_model, 0.0, est_p_tokens, est_c_tokens, savings, f"Caché Semántica (Sim Match: {best_sim*100:.0f}%)"),
            )
            conn.commit()
            
            # Cabeceras de Respuesta para Cache Hit
            _set_response_header(response, "X-Model-Selected", final_model)
            _set_response_header(response, "X-Actions-Applied", "cache_hit")
            _set_response_header(response, "X-Routing-Restriction", routing_restriction)
            _set_response_header(response, "X-Sensitive-Data-Detected", ",".join(detected_types) if detected_types else "none")
            _set_response_header(response, "X-FinOps-Cache", "hit")
            _set_response_header(response, "X-Routing-Reason", f"Caché Semántica Hit ({best_sim*100:.0f}% similitud)")
            
            usage_data = {
                "prompt_tokens": est_p_tokens,
                "completion_tokens": est_c_tokens,
                "total_tokens": est_p_tokens + est_c_tokens,
            }
            return _build_response(final_model, cached_response, usage_data, f"chatcmpl-{uuid4()}")

        # 3. Llamar al proveedor y manejar Fallback en caso de error
        llm_result = await llamar_proveedor_ia(final_model, final_prompt)
        response_text = llm_result.get("response", "")
        
        # Detectar error del proveedor
        if response_text.startswith("Error en el proveedor de IA"):
            FALLBACK_MODELS = {
                "claude-opus-4.7": "gpt-5.4-mini",
                "gpt-5.4-mini": "llama-3.1-8b-instant",
                "llama-3.1-8b-instant": "llama3.2:3b",
                "llama3.2:3b": "mistral:7b",
                "mistral:7b": "llama3.2:3b"
            }
            fallback_model = FALLBACK_MODELS.get(final_model, "llama3.2:3b")
            logger.warning(f"[PROXY] Falló llamada a '{final_model}'. Iniciando fallback automático a '{fallback_model}'...")
            
            llm_result_fb = await llamar_proveedor_ia(fallback_model, final_prompt)
            response_text_fb = llm_result_fb.get("response", "")
            
            if not response_text_fb.startswith("Error en el proveedor de IA"):
                logger.info(f"[PROXY] Fallback exitoso a '{fallback_model}'.")
                applied_actions.append(f"fallback_{final_model}_to_{fallback_model}")
                final_model = fallback_model
                response_text = response_text_fb
                llm_result = llm_result_fb
                routing_reason += f" | Fallback aplicado desde modelo caído."
            else:
                logger.error(f"[PROXY] Fallback a '{fallback_model}' falló también.")
                applied_actions.append(f"fallback_failed_{fallback_model}")
        
        cost_usd = float(llm_result.get("cost_usd", 0.0) or 0.0)
        usage_data = llm_result.get("usage", {})
        prompt_tokens = int(usage_data.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage_data.get("completion_tokens", 0) or 0)
        total_tokens = int(usage_data.get("total_tokens", 0) or 0)
        
        usage_data_normalized = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

        # Calcular ahorro frente a haber usado modelo Premium (Claude Opus) por defecto
        premium_cost = ((prompt_tokens / 1000.0) * 0.005) + ((completion_tokens / 1000.0) * 0.025)
        savings = max(0.0, premium_cost - cost_usd)

        new_spend = current_spend + cost_usd
        cursor.execute(
            "UPDATE consumers SET current_spend = ? WHERE id = ?",
            (new_spend, x_consumer_id),
        )
        cursor.execute(
            """
            INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (x_consumer_id, user_prompt, response_text, final_model, cost_usd, prompt_tokens, completion_tokens, savings, routing_reason),
        )
        conn.commit()
        
        # Cabeceras de Respuesta para Cache Miss
        _set_response_header(response, "X-Model-Selected", final_model)
        _set_response_header(response, "X-Actions-Applied", ",".join(applied_actions) if applied_actions else "none")
        _set_response_header(response, "X-Routing-Restriction", routing_restriction)
        _set_response_header(response, "X-Sensitive-Data-Detected", ",".join(detected_types) if detected_types else "none")
        _set_response_header(response, "X-FinOps-Cache", "miss")
        _set_response_header(response, "X-Routing-Reason", routing_reason)
        
        return _build_response(final_model, response_text, usage_data_normalized, f"chatcmpl-{uuid4()}")
    finally:
        conn.close()
