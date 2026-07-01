import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.llm_clients import llamar_proveedor_ia


class LLMClientTests(unittest.TestCase):
    def test_mistral_model_uses_provider_b_api_base(self):
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            _hidden_params={"response_cost": 0.0},
        )

        with patch("app.llm_clients.litellm.acompletion", new=AsyncMock(return_value=fake_response)) as mock_acompletion:
            import asyncio
            asyncio.run(llamar_proveedor_ia("mistral:7b", "hi"))

        self.assertEqual(mock_acompletion.await_args.kwargs["api_base"], "http://localhost:11435")


if __name__ == "__main__":
    unittest.main()
