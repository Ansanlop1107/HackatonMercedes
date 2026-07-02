import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import chat as chat_module
from app.db import get_db_connection, init_db
from app.main import app
from app.router import DecisionRouter


class ChatEndpointTests(unittest.TestCase):
    def setUp(self):
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        conn.commit()
        conn.close()

    def test_chat_completions_returns_openai_style_payload(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO consumers (id, budget, current_spend) VALUES (?, ?, 0.0)",
            ("test-consumer", 10.0),
        )
        conn.commit()
        conn.close()

        async def fake_llamar_proveedor_ia(model_name, prompt):
            return {
                "response": "mocked answer",
                "cost_usd": 0.001,
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                },
            }

        with patch.object(chat_module, "llamar_proveedor_ia", side_effect=fake_llamar_proveedor_ia):
            client = TestClient(app)
            response = client.post(
                "/v1/chat/completions",
                headers={"X-Consumer-ID": "test-consumer"},
                json={"prompt": "Hello from payload test"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["choices"][0]["message"]["content"], "mocked answer")
        self.assertEqual(payload["usage"]["total_tokens"], 5)

    def test_complex_prompt_with_real_time_urgency_uses_premium_model(self):
        model_name, _, _, reason = DecisionRouter.evaluate_rules(
            consumer_id="mercedes-analytics-dashboard",
            prompt="Necesito un análisis complejo de algoritmos y lógica para justificar una decisión",
            requested_model="gpt-5.4-mini",
            current_spend=0.0,
            budget=100.0,
            has_justification=True,
            urgency="real-time",
        )

        self.assertEqual(model_name, "claude-opus-4.7")
        self.assertIn("compleja", reason.lower())

    def test_chat_completions_accepts_non_latin1_header_values(self):
        init_db()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO consumers (id, budget, current_spend) VALUES (?, ?, 0.0)",
            ("test-consumer", 10.0),
        )
        conn.commit()
        conn.close()

        async def fake_llamar_proveedor_ia(model_name, prompt):
            return {
                "response": "mocked answer",
                "cost_usd": 0.001,
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 2,
                    "total_tokens": 5,
                },
            }

        with patch.object(chat_module, "llamar_proveedor_ia", side_effect=fake_llamar_proveedor_ia), patch.object(
            chat_module.DecisionRouter,
            "evaluate_rules",
            return_value=(
                "gpt-5.4-mini",
                "Hello",
                [],
                "⚡ LATENCIA: Requisito urgente (real-time). Enrutado a Groq LPU (Llama 3.1).",
            ),
        ):
            client = TestClient(app)
            response = client.post(
                "/v1/chat/completions",
                headers={"X-Consumer-ID": "test-consumer"},
                json={"prompt": "Hello from header test"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("x-routing-reason", response.headers)


if __name__ == "__main__":
    unittest.main()
