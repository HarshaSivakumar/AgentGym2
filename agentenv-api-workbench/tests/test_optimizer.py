import json
import tempfile
import unittest
from pathlib import Path

from agentenv_api_workbench.optimizer import PromptOptimizer, propose_prompt


class _FakeModel:
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, None]:
        self.conversation = conversation
        return "revised instructions", None


class PromptOptimizerTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()