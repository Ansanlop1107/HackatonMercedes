import logging
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

        routing_restriction, _ = SecurityLayer.evaluate_security(user_prompt)

        logger.info(
            f"[PROXY] Consumidor: {x_consumer_id} | Presupuesto: ${budget:.2f} | Gasto Actual: ${current_spend:.6f}"
        )
        if current_spend >= budget:
            logger.warning(
                f"[PROXY] Consumidor '{x_consumer_id}' excedió su presupuesto (${current_spend:.6f}/${budget:.2f}). Petición bloqueada."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Presupuesto excedido. Solicite una ampliación de crédito FinOps.",
            )

        requested_model = request.model or "gpt-5.4-mini"
        final_model, final_prompt, _ = DecisionRouter.evaluate_rules(
            consumer_id=x_consumer_id,
            prompt=user_prompt,
            requested_model=requested_model,
            current_spend=current_spend,
            budget=budget,
            has_justification=bool(x_justification),
            routing_restriction=routing_restriction,
        )

        cached_response = None
        if routing_restriction == "force_local":
            cursor.execute(
                """
                SELECT response, model_used FROM logs
                WHERE prompt = ? AND timestamp >= datetime('now', '-24 hours')
                  AND model_used IN ('llama3.2:3b', 'mistral:7b')
                ORDER BY timestamp DESC LIMIT 1
                """,
                (user_prompt,),
            )
            cached_row = cursor.fetchone()
            if cached_row:
                cached_response = cached_row["response"]
                final_model = cached_row["model_used"] or final_model

        if cached_response is not None:
            usage_data = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            cursor.execute(
                """
                INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (x_consumer_id, user_prompt, cached_response, final_model, 0.0),
            )
            conn.commit()
            response.headers["X-FinOps-Cache"] = "hit"
            return _build_response(final_model, cached_response, usage_data, f"chatcmpl-{uuid4()}")

        llm_result = await llamar_proveedor_ia(final_model, final_prompt)
        response_text = llm_result.get("response", "")
        cost_usd = float(llm_result.get("cost_usd", 0.0) or 0.0)
        usage_data = llm_result.get("usage", {})
        usage_data = {
            "prompt_tokens": int(usage_data.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage_data.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage_data.get("total_tokens", 0) or 0),
        }

        new_spend = current_spend + cost_usd
        cursor.execute(
            "UPDATE consumers SET current_spend = ? WHERE id = ?",
            (new_spend, x_consumer_id),
        )
        cursor.execute(
            """
            INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (x_consumer_id, user_prompt, response_text, final_model, cost_usd),
        )
        conn.commit()
        response.headers["X-FinOps-Cache"] = "miss"
        return _build_response(final_model, response_text, usage_data, f"chatcmpl-{uuid4()}")
    finally:
        conn.close()
