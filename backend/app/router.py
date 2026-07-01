import logging
from typing import Tuple, List
# Propiedades y tarifas de precios de los modelos (costes por cada 1,000 tokens)
MODELS_PROPERTIES = {
    "claude-opus-4.7": {
        "input_cost": 0.005,       # $5.00 por 1M tokens
        "output_cost": 0.025,      # $25.00 por 1M tokens
        "latency_ms": 1500,
        "tier": "premium"
    },
    "gpt-5.4-mini": {
        "input_cost": 0.00075,     # $0.75 por 1M tokens
        "output_cost": 0.00450,    # $4.50 por 1M tokens
        "latency_ms": 300,
        "tier": "standard"
    },
    "mistral:7b": {
        "input_cost": 0.00024,     # $0.24 por 1M tokens
        "output_cost": 0.00024,
        "latency_ms": 300,
        "tier": "standard"
    },
    "llama-3.1-8b-instant": {
        "input_cost": 0.00005,     # $0.05 por 1M tokens
        "output_cost": 0.00008,    # $0.08 por 1M tokens
        "latency_ms": 150,
        "tier": "economy"
    },
    "llama3.2:3b": {
        "input_cost": 0.00006,     # $0.06 por 1M tokens
        "output_cost": 0.00006,
        "latency_ms": 100,
        "tier": "economy"
    }
}

logger = logging.getLogger("ai_finops_proxy.router")

# Clasificación de los consumidores y sus prioridades según el diseño
CONSUMER_PRIORITIES = {
    "mercedes-drive-assistant": "critical",
    "mercedes-analytics-dashboard": "standard",
    "mercedes-lab-experiments": "experimental"
}

class DecisionRouter:
    @staticmethod
    def evaluate_rules(
        consumer_id: str,
        prompt: str,
        requested_model: str,
        current_spend: float,
        budget: float,
        has_justification: bool,
        routing_restriction: str = "delegate_to_finops"
    ) -> Tuple[str, str, List[str]]:
        """
        Evalúa de forma secuencial las reglas FinOps (WHO, WHAT, WHEN, WHY) y
        retorna el modelo final, el prompt optimizado y la lista de acciones aplicadas.
        
        Retorna:
          (final_model, final_prompt, applied_actions)
        """
        applied_actions = []
        final_prompt = prompt
        
        # Validar existencia del modelo solicitado en nuestra configuración
        if requested_model not in MODELS_PROPERTIES:
            requested_model = "gpt-5.4-mini"  # Fallback a estándar
            
        final_model = requested_model

        # --- REGLA: CAPA 1 - SEGURIDAD (DLP force_local) ---
        if routing_restriction == "force_local":
            applied_actions.append("force_local_model")
            # Si el modelo solicitado ya es local, se mantiene. Si no, se fuerza llama3.2:3b
            if requested_model in ["llama3.2:3b", "mistral:7b"]:
                final_model = requested_model
            else:
                final_model = "llama3.2:3b"
            logger.info(f"[ROUTER] [SECURITY] Restricción 'force_local' activa. Enrutando a modelo local '{final_model}'.")
            return final_model, final_prompt, applied_actions
        
        # 1. Obtener la prioridad del consumidor (WHO)
        priority = CONSUMER_PRIORITIES.get(consumer_id, "standard")
        
        # --- REGLA: WHEN (Presupuesto acumulado > 80%) ---
        budget_usage = (current_spend / budget) if budget > 0 else 0.0
        if budget_usage > 0.80:
            applied_actions.append("activate_savings_mode")
            # Activación forzada de ahorro: enruta a modelo económico local
            final_model = "llama3.2:3b"
            logger.warning(f"[ROUTER] [WHEN] Ahorro Activo (budget_usage = {budget_usage*100:.1f}%). Forzando economía.")
            return final_model, final_prompt, applied_actions

        # --- REGLA: WHO (Prioridad del consumidor) ---
        if priority == "critical":
            applied_actions.append("allow")
            # El crítico tiene permiso inicial para usar lo solicitado, pero sigue evaluando tokens
        elif priority == "experimental":
            applied_actions.append("force_low_cost_model")
            final_model = "llama3.2:3b"
            logger.info("[ROUTER] [WHO] Consumidor Experimental detectado. Forzando modelo económico.")
            # Forzamos modelo económico y detenemos degradaciones adicionales
        else:  # priority == "standard"
            applied_actions.append("reroute")
            # Standard se le permite avanzar pero está sujeto a re-enrutamiento por costes/justificación

        # --- REGLA: WHAT (Tokens estimados) ---
        # Estimar tokens basado en que 1 palabra ≈ 1.3 tokens en promedio
        words = len(final_prompt.split())
        estimated_tokens = int(words * 1.3)
        
        if estimated_tokens > 32000:
            # Acción obligatoria: Requerir justificación (se validará en el controlador)
            applied_actions.append("request_justification")
        elif estimated_tokens > 8000:
            # Si supera 8,000 tokens (límite soft) pero no 32,000, simplemente registramos la acción.
            # No truncamos ni reescribimos el prompt para no perder información valiosa del usuario.
            applied_actions.append("auto_prompt_rewrite")
            logger.info(f"[ROUTER] [WHAT] Prompt supera el límite blando de 8000 tokens ({estimated_tokens} tokens). No se realiza truncado por política de integridad de datos.")

        # Si el modelo final ya fue forzado a económico por prioridad experimental, omitimos reglas de premium/coste
        if final_model == "llama3.2:3b":
            return final_model, final_prompt, applied_actions

        # --- REGLA: WHY (Justificación de modelo Premium) ---
        props = MODELS_PROPERTIES[final_model]
        if props["tier"] == "premium" and not has_justification:
            applied_actions.append("degrade_model")
            # Degradación a estándar gpt-5.4-mini
            final_model = "gpt-5.4-mini"
            logger.info(f"[ROUTER] [WHY] Modelo Premium solicitado sin justificación. Degradando a '{final_model}'.")
            props = MODELS_PROPERTIES[final_model]  # Actualizar propiedades

        # --- REGLA: WHAT (Límite de Coste por Petición > $0.10) ---
        # Estimar coste considerando un baseline de 500 tokens de salida para la estimación previa
        est_input_cost = (estimated_tokens / 1000.0) * props["input_cost"]
        est_output_cost = (500 / 1000.0) * props["output_cost"]
        estimated_cost = est_input_cost + est_output_cost
        
        if estimated_cost > 0.10 and priority != "critical":
            # Si supera los $0.10 y no es crítico, degradamos/re-enrutamos a un modelo más barato
            old_model = final_model
            if props["tier"] == "premium":
                final_model = "gpt-5.4-mini"
            elif props["tier"] == "standard":
                final_model = "llama-3.1-8b-instant"
            applied_actions.append("reroute_cost_threshold")
            logger.info(f"[ROUTER] [WHAT] Coste estimado ${estimated_cost:.4f} supera $0.10. Re-enrutando '{old_model}' -> '{final_model}'.")

        return final_model, final_prompt, applied_actions
