# -*- coding: utf-8 -*-
import sqlite3
import random
import os
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finops.db")

TEAMS = {
    # Alta Prioridad
    "ingenieria-desarrollo": {"budget": 150.00, "priority": "critical"},
    "legal-compliance": {"budget": 100.00, "priority": "critical"},
    "datos-ia": {"budget": 100.00, "priority": "critical"},
    "direccion-estrategia": {"budget": 200.00, "priority": "critical"},
    # Media Prioridad
    "marketing-contenidos": {"budget": 50.00, "priority": "standard"},
    "ventas": {"budget": 50.00, "priority": "standard"},
    "producto": {"budget": 50.00, "priority": "standard"},
    "finanzas": {"budget": 75.00, "priority": "standard"},
    # Baja Prioridad
    "atencion-cliente": {"budget": 15.00, "priority": "experimental"},
    "recursos-humanos": {"budget": 15.00, "priority": "experimental"},
    "soporte-ti": {"budget": 15.00, "priority": "experimental"},
    "administracion-operaciones": {"budget": 20.00, "priority": "experimental"},
    # Existentes
    "equipo-marketing": {"budget": 10.00, "priority": "standard"},
    "equipo-producto": {"budget": 10.00, "priority": "standard"},
}

MODELS = ["claude-opus-4.7", "gpt-5.4-mini", "llama-3.1-8b-instant", "llama3.2:3b", "mistral:7b"]

PROMPTS = [
    "Refactorizar funcion recursiva para calcular Fibonacci con memoizacion.",
    "Analizar clausula de indemnizacion en contrato de prestacion de servicios cloud.",
    "Extraer la correlacion lineal entre las columnas de ventas y publicidad del CSV.",
    "Resumen ejecutivo de los resultados financieros del segundo trimestre.",
    "Redactar copia publicitaria para la nueva campaña de coches electricos.",
    "Escribir correo de seguimiento para cliente potencial interesado en el plan Pro.",
    "Crear historias de usuario para el sprint 12 sobre integracion de pasarela de pago.",
    "Clasificar los gastos de viaje de la ultima semana segun categoria contable.",
    "Ayuda, mi usuario no puede acceder al portal de soporte de TI interno.",
    "Redactar oferta de empleo para el puesto de Senior Fullstack Engineer en Madrid.",
    "Como configurar la VPN de la empresa en un equipo con MacOS Sonoma?",
    "Corregir ortografia y traducir comunicado interno de recursos humanos al ingles."
]

RESPONSES = [
    "Aqui tienes la funcion optimizada utilizando decoradores de cache de Python.",
    "La clausula analizada limita la responsabilidad al 100% de los honorarios pagados.",
    "El coeficiente de correlacion de Pearson es de 0.85, indicando una fuerte relacion.",
    "Los ingresos netos aumentaron un 15% interanual superando las previsiones de mercado.",
    "Descubre la revolucion de la movilidad electrica. Eficiencia y diseño premium.",
    "Hola, te escribo para saber si tuviste tiempo de revisar nuestra propuesta comercial.",
    "Como usuario administrador, quiero poder ver el panel de control FinOps...",
    "Los gastos han sido clasificados como: 45% alojamiento, 35% comida and 20% transporte.",
    "Por favor, asegurate de limpiar las cookies del navegador e intentar de nuevo.",
    "Buscamos un Ingeniero de Software con mas de 5 años de experiencia en React y Python...",
    "Para configurar la VPN en macOS: 1. Abre Preferencias del Sistema -> Red...",
    "Please find below the translated internal communication in English..."
]

REASONS = [
    "NLP: Tarea compleja/logica con justificacion. Enrutado a Claude Opus.",
    "DLP: Contiene datos personales o PII. Forzado modelo local Llama3.2.",
    "MODALIDAD: Analisis de datos. Enrutado a GPT-5.4-mini.",
    "LATENCIA: Requisito urgente (real-time). Enrutado a Groq LPU.",
    "CONTEXTO: Contexto largo. Enrutado a Llama 3.1 8b en Groq.",
    "NLP: Tarea estandar/sencilla. Enrutado a modelo economico Llama 3.1 8b.",
]

def seed():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Limpiar tablas
    cursor.execute("DELETE FROM logs")
    cursor.execute("DELETE FROM consumers")
    
    print("Limpieza de base de datos realizada.")
    
    # Insertar consumidores
    for name, info in TEAMS.items():
        cursor.execute(
            "INSERT INTO consumers (id, budget, current_spend) VALUES (?, ?, 0.0)",
            (name, info["budget"])
        )
        
    print(f"Insertados {len(TEAMS)} consumidores.")
    
    start_time = datetime.now() - timedelta(days=7)
    log_entries = []
    
    for team, info in TEAMS.items():
        budget = info["budget"]
        
        # Determinar el gasto objetivo
        if team == "ventas":
            target_spend = random.uniform(50.15, 52.50)
        elif team == "ingenieria-desarrollo":
            target_spend = budget * random.uniform(0.81, 0.88)
        else:
            target_spend = budget * random.uniform(0.15, 0.70)
            
        current_team_spend = 0.0
        iterations = 0
        
        while current_team_spend < target_spend and iterations < 1500:
            iterations += 1
            
            # Si el equipo tiene prioridad experimental, forzamos modelo local
            if info["priority"] == "experimental":
                model = random.choice(["llama3.2:3b", "llama-3.1-8b-instant"])
                p_tokens = random.randint(100, 1500)
                c_tokens = random.randint(100, 2000)
            else:
                model = random.choice(MODELS)
                # Simular contextos corporativos medianos/grandes (análisis de documentos/código)
                p_tokens = random.randint(8000, 32000)
                c_tokens = random.randint(500, 3000)
                
            # Calcular coste segun el modelo con tarifas realistas
            if model == "claude-opus-4.7":
                cost = (p_tokens / 1000.0) * 0.015 + (c_tokens / 1000.0) * 0.075
            elif model == "gpt-5.4-mini":
                cost = (p_tokens / 1000.0) * 0.002 + (c_tokens / 1000.0) * 0.008
            elif model == "mistral:7b":
                cost = (p_tokens / 1000.0) * 0.00025 + (c_tokens / 1000.0) * 0.00025
            elif model == "llama-3.1-8b-instant":
                cost = (p_tokens / 1000.0) * 0.00015 + (c_tokens / 1000.0) * 0.0002
            else: # llama3.2:3b
                cost = (p_tokens / 1000.0) * 0.0001 + (c_tokens / 1000.0) * 0.0001
                
            saved_by_cache = random.choice([0, 0, 0, 0, 1]) if current_team_spend > 2.0 else 0
            if saved_by_cache:
                cost = 0.0
                savings = (p_tokens / 1000.0) * 0.015 + (c_tokens / 1000.0) * 0.075
                reason = "Cache Semantica Hit (Sim Match: 88%)"
            else:
                premium_cost = (p_tokens / 1000.0) * 0.015 + (c_tokens / 1000.0) * 0.075
                savings = max(0.0, premium_cost - cost)
                reason = random.choice(REASONS)
                
            log_time = start_time + timedelta(hours=random.randint(1, 160))
            
            prompt = random.choice(PROMPTS)
            response = random.choice(RESPONSES)
            
            log_entries.append((
                log_time.strftime("%Y-%m-%d %H:%M:%S"),
                team,
                prompt,
                response,
                model,
                cost,
                saved_by_cache,
                p_tokens,
                c_tokens,
                savings,
                reason
            ))
            current_team_spend += cost
            
    # Insertar logs
    cursor.executemany(
        """
        INSERT INTO logs (timestamp, consumer_id, prompt, response, model_used, cost, saved_by_cache, prompt_tokens, completion_tokens, savings, routing_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        log_entries
    )
    
    print(f"Insertados {len(log_entries)} logs historicos.")
    
    # Calcular y actualizar current_spend para cada consumidor
    for team in TEAMS.keys():
        cursor.execute("SELECT SUM(cost) FROM logs WHERE consumer_id = ?", (team,))
        total_spent = cursor.fetchone()[0] or 0.0
        cursor.execute("UPDATE consumers SET current_spend = ? WHERE id = ?", (total_spent, team))
        
    conn.commit()
    conn.close()
    print("Base de datos de FinOps poblada con exito con datos historicos reales.")

if __name__ == "__main__":
    seed()
