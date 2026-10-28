import json
import tempfile
import unittest
from pathlib import Path

from agentenv_api_workbench.optimizer import PromptOptimizer, propose_prompt
from agentenv_api_workbench.optimize import resolve_state_path


class _FakeModel:
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, None]:
        self.conversation = conversation
        return "revised instructions", None


class _FakeEvaluationReport:
    def __init__(self, score: float, task_id: str) -> None:
        self.score = score
        self.task_id = task_id

    def to_dict(self) -> dict[str, object]:
        return {"score": self.score, "task_results": [{"task_id": self.task_id}]}


class _FakeEvaluator:
    def __init__(self, score: float, task_id: str) -> None:
        self.score = score
        self.task_id = task_id

    def evaluate(self, prompt: str) -> _FakeEvaluationReport:
        return _FakeEvaluationReport(self.score, self.task_id)


class PromptOptimizerTests(unittest.TestCase):
    def test_default_state_path_is_package_relative(self) -> None:
        path = resolve_state_path(None, "api_design")

        self.assertEqual(
            path,
            Path(__file__).resolve().parents[1]
            / "runs"
            / "api_design-optimizer.json",
        )

    def test_accepts_improvements_and_rejects_regressions(self) -> None:
        scores = {"base": 0.5, "worse": 0.2, "better": 0.8}
        candidates = iter(("worse", "better"))
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "history.json"
            result = PromptOptimizer(state_path).run(
                initial_prompt="base",
                score_prompt=scores.__getitem__,
                proposer=lambda prompt, score, history: next(candidates),
                iterations=2,
            )

            saved_history = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(result.best_prompt, "better")
        self.assertEqual(result.best_score, 0.8)
        self.assertFalse(result.history[1]["accepted"])
        self.assertTrue(result.history[2]["accepted"])
        self.assertEqual(saved_history, list(result.history))

    def test_propose_prompt_sends_current_score_and_instructions(self) -> None:
        model = _FakeModel()

        candidate = propose_prompt(model, "base instructions", 0.75, [])

        self.assertEqual(candidate, "revised instructions")
        self.assertIn("0.750", model.conversation[1]["content"])
        self.assertIn("base instructions", model.conversation[1]["content"])

    def test_validation_regression_rejects_training_improvement(self) -> None:
        train_scores = {"base": 0.5, "candidate": 1.0}
        validation_scores = {"base": 0.8, "candidate": 0.4}

        with tempfile.TemporaryDirectory() as temp_dir:
            result = PromptOptimizer(Path(temp_dir) / "history.json").run(
                initial_prompt="base",
                score_prompt=train_scores.__getitem__,
                validation_score_prompt=validation_scores.__getitem__,
                proposer=lambda prompt, score, history: "candidate",
                iterations=1,
            )

        self.assertEqual(result.best_prompt, "base")
        self.assertEqual(result.best_train_score, 0.5)
        self.assertEqual(result.best_score, 0.8)
        self.assertEqual(result.history[1]["train_score"], 1.0)
        self.assertEqual(result.history[1]["validation_score"], 0.4)
        self.assertFalse(result.history[1]["accepted"])

    def test_persists_per_task_train_and_validation_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "history.json"
            result = PromptOptimizer(state_path).run(
                initial_prompt="base",
                score_prompt=_FakeEvaluator(0.75, "train-task"),
                validation_score_prompt=_FakeEvaluator(1.0, "held-out-task"),
                proposer=lambda prompt, score, history: "unused",
                iterations=0,
            )
            saved = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(result.best_train_score, 0.75)
        self.assertEqual(result.best_score, 1.0)
        self.assertEqual(result.best_train_report["task_results"][0]["task_id"], "train-task")
        self.assertEqual(
            result.best_validation_report["task_results"][0]["task_id"], "held-out-task"
        )
        self.assertEqual(
            saved[0]["validation_report"]["task_results"][0]["task_id"],
            "held-out-task",
        )


if __name__ == "__main__":
    unittest.main()