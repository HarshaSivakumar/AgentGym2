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
        return {"task_id": f"fixture-{index}", "observation": f"fixture {index}"}

    def step(self, action: str) -> StepOutput:
        self.info = {
            "info": {
                "passed_checks": [f"check-{self.index}"],
                "failed_checks": ["missing-section"] if self.index == 1 else [],
            }
        }
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

    @patch("agentenv_api_workbench.evaluation.ApiWorkbenchEnvClient", _FakeClient)
    def test_report_contains_each_task_score_and_rubric_details(self) -> None:
        evaluator = WorkbenchEvaluator(
            agent=_FakeModel(),
            env_server_base="http://localhost",
            agent_mode="api_design",
            plugin_root="unused-in-fake",
            task_indices=(1,),
        )

        report = evaluator.evaluate("optimized instructions")

        self.assertEqual(report.score, 1.0)
        self.assertEqual(len(report.task_results), 1)
        self.assertEqual(report.task_results[0].task_id, "fixture-1")
        self.assertEqual(report.task_results[0].passed_checks, ("check-1",))
        self.assertEqual(report.task_results[0].failed_checks, ("missing-section",))
        self.assertEqual(report.to_dict()["task_results"][0]["score"], 1.0)


class TaskSplitTests(unittest.TestCase):
    def test_last_fixture_is_held_out_for_validation(self) -> None:
        from agentenv_api_workbench.evaluation import split_task_indices

        train_indices, validation_indices = split_task_indices(3)

        self.assertEqual(train_indices, (0, 1))
        self.assertEqual(validation_indices, (2,))

    def test_split_rejects_too_few_tasks(self) -> None:
        from agentenv_api_workbench.evaluation import split_task_indices

        with self.assertRaises(ValueError):
            split_task_indices(1)


if __name__ == "__main__":
    unittest.main()