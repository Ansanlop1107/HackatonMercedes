import re
import logging
from typing import Tuple, List
from fastapi import HTTPException, status

from app.db import get_db_connection

logger = logging.getLogger("ai_finops_proxy.security")

# 1. Palabras clave a bloquear para evitar Prompt Injection (case-insensitive)
PROMPT_INJECTION_KEYWORDS = [
    "ignora", 
    "bypass", 
    "system prompt", 
    "olvida las instrucciones", 
    "desarrollador", 
    "dan", 
    "prompt original"
]

# 2. Expresiones regulares muy precisas para DLP (Data Loss Prevention)
DLP_REGEXES = {
    "matricula_espanola": re.compile(r"\b\d{4}[- ]?[B-DF-HJ-NP-TV-Z]{3}\b", re.IGNORECASE),      # Modernas (ej: 1234 ABC, 1234-ABC)
    "matricula_espanola_antigua": re.compile(r"\b[A-Z]{1,2}[- ]?\d{4}[- ]?[A-Z]{1,2}\b", re.IGNORECASE), # Antiguas (ej: M-1234-AZ)
    "vin_bastidor": re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.IGNORECASE),                        # 17 caracteres alfanuméricos estandarizados
    "dni_nie_espanol": re.compile(r"\b(?:\d{8}|[XYZ]\d{7})[- ]?[A-Z]\b", re.IGNORECASE),          # DNI/NIE españoles
    "iban_espanol": re.compile(r"\bES\d{2}(?:[ -]?\d{4}){5}\b", re.IGNORECASE),                   # Cuentas bancarias IBAN españolas
    "telefono": re.compile(r"\b(?:\+?\d{1,3}[- ]?)?\(?\d{2,3}\)?[- ]?\d{3,4}[- ]?\d{3,4}\b"),     # Teléfonos españoles/internacionales
    "email": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),                   # Correos electrónicos
    "tarjeta_credito": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),                                 # Tarjetas de crédito de 16 dígitos
    "ip_privada": re.compile(
        r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3})|"
        r"(?:192\.168\.\d{1,3}\.\d{1,3})|"
        r"(?:172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
    ) # Direcciones IP privadas (RFC 1918)
}

class SecurityLayer:
    @staticmethod
    def check_prompt_injection(prompt: str) -> None:
        """
        Analiza si el prompt contiene intentos de Prompt Injection.
        Si detecta alguna palabra prohibida, lanza inmediatamente HTTPException 403.
        """
        prompt_lower = prompt.lower()
        for keyword in PROMPT_INJECTION_KEYWORDS:
            if keyword in prompt_lower:
                logger.error(f"[SECURITY] Intento de Prompt Injection detectado. Palabra clave prohibida: '{keyword}'")
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO logs (consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason, event_type) VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0.0, ?, ?)",
                    ('unknown', prompt, 'Prompt injection bloqueado', 'blocked', 0.0, 'Intento de prompt injection detectado', 'blocked_security'),
                )
                conn.commit()
                conn.close()
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="ALERTA CRÍTICA: Intento de manipulación del sistema (Prompt Injection) bloqueado"
                )

    @staticmethod
    def scan_dlp(prompt: str) -> Tuple[bool, List[str]]:
        """
        Escanea el prompt utilizando expresiones regulares para detectar datos sensibles.
        Retorna un booleano contains_sensitive_data y la lista de tipos detectados.
        """
        contains_sensitive_data = False
        detected_types = []
        
        for name, regex in DLP_REGEXES.items():
            matches = regex.findall(prompt)
            if matches:
                contains_sensitive_data = True
                detected_types.append(name)
                logger.warning(f"[SECURITY] [DLP] Dato sensible detectado tipo '{name}'. Coincidencias: {len(matches)}")
                
        return contains_sensitive_data, detected_types

    @classmethod
    def evaluate_security(cls, prompt: str) -> Tuple[str, List[str]]:
        """
        Función principal de la Capa 1 de Seguridad.
        Analiza inyecciones y DLP, devolviendo la restricción de enrutado.
        
        Retorna:
          (routing_restriction, detected_types)
        """
        # 1. Firewall: Bloqueo de Prompt Injection (lanza 403 si falla)
        cls.check_prompt_injection(prompt)
        
        # 2. DLP: Detección de datos sensibles
        contains_sensitive_data, detected_types = cls.scan_dlp(prompt)
        
        # 3. Lógica de Decisión (routing_restriction)
        if contains_sensitive_data:
            routing_restriction = "force_local"
            logger.info(f"[SECURITY] Capa 1 finalizada. Restricción establecida: 'force_local'")
        else:
            routing_restriction = "delegate_to_finops"
            logger.info("[SECURITY] Capa 1 finalizada. Restricción establecida: 'delegate_to_finops'")
            
        return routing_restriction, detected_types
