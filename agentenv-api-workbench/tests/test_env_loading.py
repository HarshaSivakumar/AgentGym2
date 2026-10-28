import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentenv_api_workbench.config import load_environment
from agentenv_api_workbench.optimize import _required_environment


class EnvironmentLoadingTests(unittest.TestCase):
    def test_loads_dotenv_values_without_overriding_shell_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "OPENAI_MODEL=dotenv-model\nOPENAI_API_KEY=test-only-key\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"OPENAI_MODEL": "shell-model"}, clear=True):
                load_environment(env_file)

                self.assertEqual(os.environ["OPENAI_MODEL"], "shell-model")
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-only-key")

    def test_resolves_azure_standard_key_and_deployment_names(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test-only-key",
                "AZURE_OPENAI_DEPLOYMENT": "test-deployment",
            },
            clear=True,
        ):
            api_key = _required_environment("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY")
            deployment = _required_environment("OPENAI_MODEL", "AZURE_OPENAI_DEPLOYMENT")

        self.assertEqual(api_key, "test-only-key")
        self.assertEqual(deployment, "test-deployment")


if __name__ == "__main__":
    unittest.main()