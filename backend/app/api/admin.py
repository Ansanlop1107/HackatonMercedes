import logging
import sqlite3
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_db_connection
import pandas as pd

logger = logging.getLogger("ai_finops_proxy.api.admin")

router = APIRouter(prefix="/v1/admin", tags=["Admin"])

class LoginRequest(BaseModel):
    username: str
    password: str

class BudgetUpdateRequest(BaseModel):
    budget: float

class ConsumerCreateRequest(BaseModel):
    id: str
    budget: float

@router.post("/login")
async def login(req: LoginRequest):
    """
    Endpoint de login simple.
    - admin / admin -> Acceso como Administrador.
    - id_departamento / id_departamento -> Acceso como Usuario (consulta departamento).
    """
    username = req.username.strip()
    password = req.password.strip()

    if username == "admin" and password == "admin":
        logger.info("[AUTH] Administrador ha iniciado sesión.")
        return {"status": "success", "username": "admin", "role": "admin"}
    
    # Comprobar si coincide con un departamento existente en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM consumers WHERE id = ?", (username,))
    consumer = cursor.fetchone()
    conn.close()
    
    if consumer and password == username:
        logger.info(f"[AUTH] Usuario del departamento '{username}' ha iniciado sesión.")
        return {"status": "success", "username": username, "role": "user"}
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario o contraseña incorrectos."
    )

@router.get("/consumers")
async def list_consumers():
    """
    Retorna la lista de todos los consumidores (departamentos), sus presupuestos y gasto actual.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, budget, current_spend FROM consumers")
        consumers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return consumers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener consumidores: {str(e)}"
        )

@router.post("/consumers")
async def create_consumer(req: ConsumerCreateRequest):
    """
    Crear un nuevo departamento/consumidor en la base de datos.
    """
    consumer_id = req.id.strip()
    if not consumer_id:
        raise HTTPException(status_code=400, detail="El ID del departamento no puede estar vacío.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO consumers (id, budget, current_spend) VALUES (?, ?, 0.0)",
            (consumer_id, req.budget)
        )
        conn.commit()
        logger.info(f"[ADMIN] Creado nuevo departamento '{consumer_id}' con presupuesto ${req.budget:.2f}")
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"El departamento '{consumer_id}' ya está registrado."
        )
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Error creando departamento: {str(e)}"
        )
    conn.close()
    return {"status": "success", "message": f"Departamento '{consumer_id}' registrado correctamente."}

@router.put("/consumers/{consumer_id}/budget")
async def update_budget(consumer_id: str, req: BudgetUpdateRequest):
    """
    Actualizar el presupuesto límite de un departamento.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM consumers WHERE id = ?", (consumer_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Departamento no encontrado.")
        
    cursor.execute(
        "UPDATE consumers SET budget = ? WHERE id = ?",
        (req.budget, consumer_id)
    )
    conn.commit()
    conn.close()
    logger.info(f"[ADMIN] Presupuesto de '{consumer_id}' actualizado a ${req.budget:.2f}")
    return {"status": "success", "message": f"Presupuesto de '{consumer_id}' actualizado correctamente."}

@router.get("/logs")
async def list_logs(consumer_id: Optional[str] = None, limit: int = 50):
    """
    Retorna la lista de logs de auditoría más recientes.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if consumer_id:
            cursor.execute("""
                SELECT id, timestamp, consumer_id, prompt, response, model_used, cost, saved_by_cache 
                FROM logs 
                WHERE consumer_id = ?
                ORDER BY id DESC 
                LIMIT ?
            """, (consumer_id, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, consumer_id, prompt, response, model_used, cost, saved_by_cache 
                FROM logs 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener logs: {str(e)}"
        )

@router.post("/reset")
async def reset_database():
    """
    Reinicia el gasto acumulado de todos los consumidores y vacía los logs.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        cursor.execute("UPDATE consumers SET current_spend = 0.0")
        conn.commit()
        conn.close()
        logger.info("[ADMIN] Base de datos reiniciada. Logs vaciados y gastos reseteados.")
        return {"status": "success", "message": "Gasto y logs reiniciados correctamente."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reiniciar la base de datos: {str(e)}"
        )

@router.get("/stats")
async def get_stats():
    """
    Obtener estadísticas globales de FinOps, incluyendo gasto total, presupuestos y logs diarios.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Agregados principales
        cursor.execute("SELECT SUM(current_spend) as total_spend, SUM(budget) as total_budget FROM consumers")
        row = cursor.fetchone()
        total_spend = row["total_spend"] if row and row["total_spend"] is not None else 0.0
        total_budget = row["total_budget"] if row and row["total_budget"] is not None else 0.0
        
        cursor.execute("SELECT COUNT(*) as total_calls, SUM(cost) as total_cost, SUM(saved_by_cache) as cache_hits FROM logs")
        row = cursor.fetchone()
        total_calls = row["total_calls"] if row and row["total_calls"] is not None else 0
        total_cost = row["total_cost"] if row and row["total_cost"] is not None else 0.0
        cache_hits = row["cache_hits"] if row and row["cache_hits"] is not None else 0
        cache_misses = total_calls - cache_hits
        
        # Estimar el ahorro debido a la caché
        cursor.execute("SELECT AVG(cost) as avg_cost FROM logs WHERE saved_by_cache = 0")
        avg_cost_row = cursor.fetchone()
        avg_cost_miss = avg_cost_row["avg_cost"] if avg_cost_row and avg_cost_row["avg_cost"] is not None else 0.005
        saved_cost = cache_hits * avg_cost_miss

        # 2. Detalle por departamento
        cursor.execute("SELECT id, budget, current_spend FROM consumers")
        departments = [dict(r) for r in cursor.fetchall()]
        
        # 3. Registros diarios para tendencias y predicciones
        cursor.execute("""
            SELECT date(timestamp) as day, consumer_id, SUM(cost) as daily_cost, COUNT(*) as call_count
            FROM logs
            GROUP BY day, consumer_id
            ORDER BY day ASC
        """)
        daily_logs = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_spend_usd": total_spend,
            "total_spend_eur": total_spend * 0.92,
            "total_budget_usd": total_budget,
            "total_budget_eur": total_budget * 0.92,
            "total_calls": total_calls,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "saved_cost_usd": saved_cost,
            "saved_cost_eur": saved_cost * 0.92,
            "departments": departments,
            "daily_logs": daily_logs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular estadísticas: {str(e)}"
        )
