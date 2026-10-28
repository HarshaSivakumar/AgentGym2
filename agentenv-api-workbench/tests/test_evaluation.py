import unittest
from unittest.mock import patch

from agentenv_api_workbench.client import StepOutput
from agentenv_api_workbench.evaluation import WorkbenchEvaluator


class _FakeClient:
    def __init__(self, **kwargs: object) -> None:
        self.system_prompt = "plugin instructions"
        self.closed = False
        self.index = 0

    def __len__(self) -> int:
        return 2

    def reset(self, index: int) -> dict[str, str]:
        self.index = index
        return {"observation": f"fixture {index}"}

    def step(self, action: str) -> StepOutput:
        return StepOutput(state="done", reward=float(self.index + 1) / 2, done=True)

    def close(self) -> dict[str, bool]:
        self.closed = True
        return {"closed": True}


class _FakeModel:
    def __init__(self) -> None:
        self.conversations: list[list[dict[str, str]]] = []

    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, None]:
        self.conversations.append(conversation)
        return "candidate output", None


class WorkbenchEvaluatorTests(unittest.TestCase):
    @patch("agentenv_api_workbench.evaluation.ApiWorkbenchEnvClient", _FakeClient)
    def test_runs_each_fixture_and_averages_scores(self) -> None:
        model = _FakeModel()
        evaluator = WorkbenchEvaluator(
            agent=model,
            env_server_base="http://localhost",
            agent_mode="api_design",
            plugin_root="unused-in-fake",
        )

        score = evaluator("optimized instructions")

        self.assertEqual(score, 0.75)
        self.assertEqual(len(model.conversations), 2)
        self.assertEqual(model.conversations[0][0]["content"], "plugin instructions")
        self.assertEqual(model.conversations[1][1]["content"], "fixture 1")


if __name__ == "__main__":
    unittest.main()