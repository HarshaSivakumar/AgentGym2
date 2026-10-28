import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from agentenv_api_workbench.llm import OpenAIChatModel
from agentenv_api_workbench.optimize import _create_model


class OpenAIChatModelTests(unittest.TestCase):
    def test_foundry_responses_endpoint_uses_v1_base_and_responses_api(self) -> None:
        responses_create = Mock(return_value=SimpleNamespace(output_text="generated"))
        client = SimpleNamespace(responses=SimpleNamespace(create=responses_create))
        openai = Mock(return_value=client)
        openai_module = types.ModuleType("openai")
        openai_module.OpenAI = openai
        endpoint = "https://example.services.ai.azure.com/openai/v1/responses"
        conversation = [{"role": "user", "content": "hello"}]

        with patch.dict(sys.modules, {"openai": openai_module}):
            model = OpenAIChatModel(
                api_key="test-key",
                model="gpt-5.4-mini",
                azure_endpoint=endpoint,
            )
            result = model.generate(conversation)

        openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://example.services.ai.azure.com/openai/v1/",
        )
        responses_create.assert_called_once_with(
            model="gpt-5.4-mini",
            input=conversation,
            max_output_tokens=4096,
        )
        self.assertEqual(result, ("generated", None))

    def test_azure_client_receives_endpoint_and_api_version(self) -> None:
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=Mock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content="generated", reasoning_content=None)
                                )
                            ]
                        )
                    )
                )
            )
        )
        azure_openai = Mock(return_value=client)
        openai_module = types.ModuleType("openai")
        openai_module.AzureOpenAI = azure_openai

        with patch.dict(sys.modules, {"openai": openai_module}):
            model = OpenAIChatModel(
                api_key="test-key",
                model="booking-deployment",
                azure_endpoint="https://example.openai.azure.com/",
                api_version="2025-01-01-preview",
            )
            response = model.generate([{"role": "user", "content": "hello"}])

        azure_openai.assert_called_once_with(
            api_key="test-key",
            azure_endpoint="https://example.openai.azure.com/",
            api_version="2025-01-01-preview",
        )
        self.assertEqual(response, ("generated", None))

    def test_azure_client_requires_api_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "api_version is required"):
            OpenAIChatModel(
                api_key="test-key",
                model="booking-deployment",
                azure_endpoint="https://example.openai.azure.com/",
            )

    @patch("agentenv_api_workbench.optimize.OpenAIChatModel")
    def test_runner_uses_azure_settings(self, model_class: Mock) -> None:
        with patch.dict(
            "os.environ",
            {
                "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
                "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
            },
            clear=True,
        ):
            _create_model("test-key", "booking-deployment", 0.1)

        model_class.assert_called_once_with(
            api_key="test-key",
            model="booking-deployment",
            azure_endpoint="https://example.openai.azure.com/",
            api_version="2025-01-01-preview",
            temperature=0.1,
        )

    @patch("agentenv_api_workbench.optimize.OpenAIChatModel")
    def test_runner_accepts_foundry_responses_endpoint_without_api_version(
        self, model_class: Mock
    ) -> None:
        endpoint = "https://example.services.ai.azure.com/openai/v1/responses"
        with patch.dict(
            "os.environ",
            {"AZURE_OPENAI_ENDPOINT": endpoint},
            clear=True,
        ):
            _create_model("test-key", "gpt-5.4-mini", 0.1)

        model_class.assert_called_once_with(
            api_key="test-key",
            model="gpt-5.4-mini",
            azure_endpoint=endpoint,
            temperature=0.1,
        )

    @patch("agentenv_api_workbench.optimize.OpenAIChatModel")
    def test_runner_keeps_generic_openai_compatible_support(self, model_class: Mock) -> None:
        with patch.dict(
            "os.environ",
            {"OPENAI_BASE_URL": "https://gateway.example/v1"},
            clear=True,
        ):
            _create_model("test-key", "model-name", 0.2)

        model_class.assert_called_once_with(
            api_key="test-key",
            model="model-name",
            base_url="https://gateway.example/v1",
            temperature=0.2,
        )


if __name__ == "__main__":
    unittest.main()