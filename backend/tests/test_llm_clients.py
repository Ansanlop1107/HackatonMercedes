import os
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

    def test_cloud_model_uses_mock_without_calling_litellm(self):
        with patch.dict(os.environ, {"MOCK_CLOUD_PROVIDERS": "true"}), patch("app.llm_clients.litellm.acompletion", new=AsyncMock()) as mock_acompletion:
            import asyncio
            result = asyncio.run(llamar_proveedor_ia("gpt-5.4-mini", "complex reasoning prompt"))

        self.assertTrue(result["response"].startswith("[MOCK-gpt-5.4-mini]"))
        self.assertEqual(mock_acompletion.await_count, 0)

    def test_llama_model_uses_real_cloud_path_when_mocking_enabled(self):
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            _hidden_params={"response_cost": 0.0},
        )

        with patch.dict(os.environ, {"MOCK_CLOUD_PROVIDERS": "true"}), patch("app.llm_clients._real_cloud_completion", new=AsyncMock(return_value=fake_response)) as mock_real_cloud:
            import asyncio
            asyncio.run(llamar_proveedor_ia("llama-3.1-8b-instant", "hi"))

        self.assertEqual(mock_real_cloud.await_count, 1)


if __name__ == "__main__":
    unittest.main()
