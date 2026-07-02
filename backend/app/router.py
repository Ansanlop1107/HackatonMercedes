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
    # Equipos de demostración existentes
    "equipo-marketing": "standard",
    "equipo-producto": "standard",
    
    # Prioridad ALTA (Acceso a Modelos Premium / Caros)
    "ingenieria-desarrollo": "critical",
    "legal-compliance": "critical",
    "datos-ia": "critical",
    "direccion-estrategia": "critical",
    
    # Prioridad MEDIA (Acceso a Modelos Estándar / Mixto)
    "marketing-contenidos": "standard",
    "ventas": "standard",
    "producto": "standard",
    "finanzas": "standard",
    
    # Prioridad BAJA (Acceso a Modelos Económicos / Rápidos)
    "atencion-cliente": "experimental",
    "recursos-humanos": "experimental",
    "soporte-ti": "experimental",
    "administracion-operaciones": "experimental"
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
        routing_restriction: str = "delegate_to_finops",
        file_name: str = None,
        file_type: str = None,
        file_size: int = 0,
        file_content: str = None,
        require_json: bool = False,
        urgency: str = "real-time"
    ) -> Tuple[str, str, List[str], str]:
        """
        Evalúa de forma secuencial y multidimensional las reglas FinOps (Security, WHO, WHAT, WHEN, WHY, NLP)
        y selecciona el modelo de destino óptimo devolviendo la justificación detallada de la decisión.
        
        Retorna:
          (final_model, final_prompt, applied_actions, routing_reason)
        """
        applied_actions = []
        final_prompt = prompt
        routing_reason = "Enrutamiento estándar óptimo."
        
        # Validar existencia del modelo solicitado
        if requested_model not in MODELS_PROPERTIES:
            requested_model = "gpt-5.4-mini"
            
        final_model = requested_model
        priority = CONSUMER_PRIORITIES.get(consumer_id, "standard")

        # --- REGLA A: Capa de Privacidad y DLP (Security compliance) ---
        if routing_restriction == "force_local":
            applied_actions.append("force_local_model")
            final_model = "llama3.2:3b"
            routing_reason = "DLP: Contiene datos personales o PII. Forzado modelo local Llama3.2 por cumplimiento GDPR."
            logger.info(f"[ROUTER] [RULE A] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA B: Presupuesto agotado o límite de ahorro (WHEN) ---
        budget_usage = (current_spend / budget) if budget > 0 else 0.0
        if budget_usage > 0.80:
            applied_actions.append("activate_savings_mode")
            final_model = "llama3.2:3b"
            routing_reason = "WHEN: Gasto departamental supera el 80% del presupuesto. Forzado modelo económico local para ahorro."
            logger.warning(f"[ROUTER] [RULE B] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA C: Prioridad de Consumidor (WHO) ---
        if priority == "experimental":
            applied_actions.append("force_low_cost_model")
            final_model = "llama3.2:3b"
            routing_reason = "WHO: Consumidor de laboratorio experimental. Forzado modelo económico local."
            logger.info(f"[ROUTER] [RULE C] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA D: Modalidad del Archivo Adjunto ---
        if file_type:
            # 1. Imagen -> GPT-5.4-mini (con soporte visión)
            if file_type.startswith("image/"):
                final_model = "gpt-5.4-mini"
                applied_actions.append("route_vision_model")
                routing_reason = f"MODALIDAD: Adjunta archivo de imagen ({file_name}). Enrutado a GPT-5.4-mini con soporte de visión."
                logger.info(f"[ROUTER] [RULE D - VISION] {routing_reason}")
                return final_model, final_prompt, applied_actions, routing_reason
                
            # 2. Análisis de datos (CSV / Excel) -> gpt-5.4-mini o claude-opus-4.7 (según complejidad)
            elif any(t in file_type for t in ["csv", "excel", "sheet", "spreadsheet"]):
                # Si es compleja y tiene justificación, usamos Claude Opus
                nlp_text = (prompt + " " + (file_content or "")).lower()
                complex_keywords = ["código", "algoritmo", "matemática", "lógica", "refactor", "optimize", "sql", "excel"]
                is_complex = any(kw in nlp_text for kw in complex_keywords)
                
                if is_complex and has_justification:
                    final_model = "claude-opus-4.7"
                    applied_actions.append("route_premium_analytical")
                    routing_reason = f"MODALIDAD: Análisis de datos complejos ({file_name}). Enrutado a Claude Opus."
                else:
                    final_model = "gpt-5.4-mini"
                    applied_actions.append("route_analytical_model")
                    routing_reason = f"MODALIDAD: Análisis de datos ({file_name}). Enrutado a GPT-5.4-mini (Code Interpreter)."
                logger.info(f"[ROUTER] [RULE D - DATA] {routing_reason}")
                return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA E: Tamaño del Contexto (Context Window) ---
        prompt_tokens = len(prompt.split()) * 1.3
        file_tokens = (len(file_content.split()) * 1.3) if file_content else (file_size / 4.0 if file_size else 0)
        total_tokens = int(prompt_tokens + file_tokens)
        
        if total_tokens > 8000:
            final_model = "llama-3.1-8b-instant"  # Groq 128k context y coste mínimo
            applied_actions.append("route_long_context_model")
            routing_reason = f"CONTEXTO: Contexto largo ({total_tokens} tokens > 8k). Enrutado a Llama 3.1 8b en Groq (128k window)."
            logger.info(f"[ROUTER] [RULE E] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA F: Formato Estricto (JSON mode) ---
        if require_json:
            final_model = "llama-3.1-8b-instant"
            applied_actions.append("route_json_model")
            routing_reason = "FORMATO: Requisito JSON estricto. Enrutado a Llama 3.1 8b (JSON mode)."
            logger.info(f"[ROUTER] [RULE F] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA G: Complejidad Semántica NLP ---
        nlp_text = (prompt + " " + (file_content or "")).lower()
        complex_keywords = ["código", "algoritmo", "matemática", "lógica", "refactor", "optimize", "complejo", "integral", "recursivo", "sql", "python", "clase", "función"]
        is_complex = any(kw in nlp_text for kw in complex_keywords)

        if is_complex:
            if has_justification:
                final_model = "claude-opus-4.7"
                applied_actions.append("route_premium_complexity")
                routing_reason = "NLP: Tarea compleja/lógica con justificación. Enrutado a Claude Opus."
            else:
                final_model = "gpt-5.4-mini"
                applied_actions.append("degrade_model")
                routing_reason = "NLP: Tarea compleja sin justificación. Degradado a GPT-5.4-mini."
            logger.info(f"[ROUTER] [RULE G] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # --- REGLA H: Requisito de Latencia / Urgencia ---
        if urgency == "real-time":
            final_model = "llama-3.1-8b-instant"  # Groq LPU fast execution
            applied_actions.append("route_low_latency_model")
            routing_reason = "LATENCIA: Requisito urgente (real-time). Enrutado a Groq LPU (Llama 3.1)."
            logger.info(f"[ROUTER] [RULE H] {routing_reason}")
            return final_model, final_prompt, applied_actions, routing_reason

        # Tareas sencillas / por defecto
        final_model = "llama-3.1-8b-instant"
        applied_actions.append("route_basic_simplicity")
        routing_reason = "NLP: Tarea estándar/sencilla. Enrutado a modelo económico Llama 3.1 8b en Groq."
        logger.info(f"[ROUTER] [RULE H - DEFAULT] {routing_reason}")
        return final_model, final_prompt, applied_actions, routing_reason
