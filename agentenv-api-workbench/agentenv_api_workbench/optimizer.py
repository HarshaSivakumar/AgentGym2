from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, Sequence


class PromptModel(Protocol):
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, str | None]: ...


ScorePrompt = Callable[[str], float]


@dataclass(frozen=True)
class OptimizationResult:
    best_prompt: str
    best_score: float
    history: tuple[dict[str, object], ...]


class PromptOptimizer:
    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)

    def run(
        self,
        initial_prompt: str,
        score_prompt: ScorePrompt,
        proposer: Callable[[str, float, Sequence[dict[str, object]]], str],
        iterations: int,
    ) -> OptimizationResult:
        if iterations < 0:
            raise ValueError("iterations cannot be negative")
        if not initial_prompt.strip():
            raise ValueError("initial_prompt cannot be empty")

        best_prompt = initial_prompt
        best_score = self._score(score_prompt(best_prompt))
        history: list[dict[str, object]] = [
            {
                "iteration": 0,
                "score": best_score,
                "accepted": True,
                "prompt": best_prompt,
            }
        ]
        self._persist(history)

        for iteration in range(1, iterations + 1):
            candidate = proposer(best_prompt, best_score, tuple(history)).strip()
            if not candidate:
                history.append(
                    {
                        "iteration": iteration,
                        "score": None,
                        "accepted": False,
                        "reason": "empty candidate",
                    }
                )
                self._persist(history)
                continue

            candidate_score = self._score(score_prompt(candidate))
            accepted = candidate_score > best_score
            history.append(
                {
                    "iteration": iteration,
                    "score": candidate_score,
                    "accepted": accepted,
                    "prompt": candidate,
                }
            )
            if accepted:
                best_prompt = candidate
                best_score = candidate_score
            self._persist(history)

        return OptimizationResult(best_prompt, best_score, tuple(history))

    def _persist(self, history: list[dict[str, object]]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
        temporary_path.replace(self.state_path)

    @staticmethod
    def _score(value: float) -> float:
        score = float(value)
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Evaluation scores must be finite values between 0 and 1")
        return score


def propose_prompt(
    model: PromptModel,
    current_prompt: str,
    current_score: float,
    history: Sequence[dict[str, object]],
) -> str:
    summary = [
        {key: value for key, value in item.items() if key != "prompt"}
        for item in history
    ]
    conversation = [
        {
            "role": "system",
            "content": (
                "Improve the agent instructions using evaluation results. "
                "Return only the complete revised instruction text. Do not "
                "include analysis, markdown fences, or claims about unavailable tools."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Current score: {current_score:.3f}\n"
                f"Evaluation history: {json.dumps(summary)}\n\n"
                f"Current instructions:\n{current_prompt}"
            ),
        },
    ]
    candidate, _ = model.generate(conversation)
    return candidate