import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import chat as chat_module
from app.db import get_db_connection, init_db
from app.main import app


class ChatEndpointTests(unittest.TestCase):
    def test_chat_completions_returns_openai_style_payload(self):
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

        with patch.object(chat_module, "llamar_proveedor_ia", side_effect=fake_llamar_proveedor_ia):
            client = TestClient(app)
            response = client.post(
                "/v1/chat/completions",
                headers={"X-Consumer-ID": "test-consumer"},
                json={"prompt": "Hello"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["choices"][0]["message"]["content"], "mocked answer")
        self.assertEqual(payload["usage"]["total_tokens"], 5)


if __name__ == "__main__":
    unittest.main()
