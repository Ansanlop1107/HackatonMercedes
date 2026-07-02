# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.api import chat as chat_module
from app.db import get_db_connection, init_db
from app.main import app
from app.router import DecisionRouter

class ChatEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Asegurar que los consumidores del test estén registrados con presupuestos limpios y logs vacíos
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        
        # Equipos para simular reglas - alineados con CONSUMER_PRIORITIES en router.py
        consumers_data = [
            ("ingenieria-desarrollo", 200.0, 0.0), # Alta prioridad (critical)
            ("marketing-contenidos", 50.0, 0.0), # Media prioridad (standard)
            ("soporte-ti", 15.0, 0.0), # Baja prioridad (experimental)
            ("test-saving", 10.0, 9.0), # Presupuesto superando el 80% ($9.0 / $10.0)
        ]
        for cid, b, cs in consumers_data:
            cursor.execute(
                "INSERT OR REPLACE INTO consumers (id, budget, current_spend) VALUES (?, ?, ?)",
                (cid, b, cs)
            )
        conn.commit()
        conn.close()

        # Mock de proveedor IA genérico para evitar llamadas a APIs reales
        async def fake_llamar_proveedor_ia(model_name, prompt):
            return {
                "response": f"mocked response from {model_name}",
                "cost_usd": 0.0001,
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 15,
                    "total_tokens": 25,
                },
            }
        
        self.patcher = patch.object(chat_module, "llamar_proveedor_ia", side_effect=fake_llamar_proveedor_ia)
        self.patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.patcher.stop()

    def test_original_openai_style_payload(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Hello"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        self.assertTrue(
            content in [
                "mocked response from Llama 3.1 8b en Groq",
                "mocked response from llama-3.1-8b-instant"
            ]
        )

    def test_rule_a_privacy_force_local_pii(self):
        # Enviamos un prompt con PII (tarjeta de crédito) para forzar local
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Mi tarjeta es 4111 1111 1111 1111"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Routing-Restriction"), "force_local")
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama3.2:3b")

    def test_rule_b_high_budget_usage(self):
        # Consumidor con >80% de presupuesto consumido (test-saving)
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "test-saving"},
            json={"prompt": "Hola"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama3.2:3b")
        self.assertTrue("WHEN" in response.headers.get("X-Routing-Reason"))

    def test_rule_c_experimental_priority(self):
        # Equipo de baja prioridad (soporte-ti es prioridad experimental)
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "soporte-ti"},
            json={"prompt": "Hola TI"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama3.2:3b")
        self.assertTrue("experimental" in response.headers.get("X-Routing-Reason").lower() or "experimental" in response.headers.get("X-Actions-Applied").lower())

    def test_rule_d_vision_modality(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Analiza esta imagen", "file_name": "foto.png", "file_type": "image/png", "file_size": 2048},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "gpt-5.4-mini")
        self.assertTrue("vision" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_d_analytical_modality(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Analiza este dataset", "file_name": "datos.csv", "file_type": "text/csv", "file_size": 4096},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "gpt-5.4-mini")
        self.assertTrue("analisis" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_e_context_size_limit(self):
        # Generar un contenido de archivo largo
        large_content = "palabra " * 7000
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Analiza esto", "file_name": "largo.txt", "file_type": "text/plain", "file_content": large_content},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama-3.1-8b-instant")
        self.assertTrue("contexto" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_f_strict_json(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Dame el resultado", "require_json": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama-3.1-8b-instant")
        self.assertTrue("json" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_g_latency_urgency(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Responde ya", "urgency": "real-time"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama-3.1-8b-instant")
        self.assertTrue("latencia" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_h_nlp_complexity_with_justification(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo", "X-Justification": "Requiero refactorizar codigo critico"},
            json={"prompt": "Escribe un algoritmo recursivo optimizado en python para grafos", "urgency": "background-task"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "claude-opus-4.7")
        self.assertTrue("complex" in response.headers.get("X-Routing-Reason").lower() or "compleja" in response.headers.get("X-Routing-Reason").lower())

    def test_rule_h_nlp_complexity_no_justification(self):
        # Para que no tome el camino por defecto de latencia de tiempo real, ponemos urgency="background-task"
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "Escribe un algoritmo recursivo optimizado en python para grafos", "urgency": "background-task"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "gpt-5.4-mini")
        self.assertTrue("degradado" in response.headers.get("X-Routing-Reason").lower() or "degrade" in response.headers.get("X-Actions-Applied").lower())

    def test_rule_h_nlp_simplicity(self):
        response = self.client.post(
            "/v1/chat/completions",
            headers={"X-Consumer-ID": "ingenieria-desarrollo"},
            json={"prompt": "hola que tal", "urgency": "background-task"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Model-Selected"), "llama-3.1-8b-instant")
        self.assertTrue("sencilla" in response.headers.get("X-Routing-Reason").lower())

if __name__ == "__main__":
    unittest.main()
