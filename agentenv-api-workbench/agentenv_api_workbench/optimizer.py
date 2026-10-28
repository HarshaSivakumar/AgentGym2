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
    best_train_score: float
    best_train_report: dict[str, object] | None
    best_validation_report: dict[str, object] | None


class PromptOptimizer:
    def __init__(self, state_path: str | Path) -> None:
        self.state_path = Path(state_path)

    def run(
        self,
        initial_prompt: str,
        score_prompt: ScorePrompt,
        proposer: Callable[[str, float, Sequence[dict[str, object]]], str],
        iterations: int,
        validation_score_prompt: ScorePrompt | None = None,
    ) -> OptimizationResult:
        if iterations < 0:
            raise ValueError("iterations cannot be negative")
        if not initial_prompt.strip():
            raise ValueError("initial_prompt cannot be empty")

        best_prompt = initial_prompt
        best_train_score, best_train_report = self._evaluate_prompt(score_prompt, best_prompt)
        if validation_score_prompt is None:
            best_validation_score, best_validation_report = best_train_score, best_train_report
        else:
            best_validation_score, best_validation_report = self._evaluate_prompt(
                validation_score_prompt, best_prompt
            )
        history: list[dict[str, object]] = [
            {
                "iteration": 0,
                "score": best_validation_score,
                "train_score": best_train_score,
                "validation_score": best_validation_score,
                "accepted": True,
                "prompt": best_prompt,
                "train_report": best_train_report,
                "validation_report": best_validation_report,
            }
        ]
        self._persist(history)

        for iteration in range(1, iterations + 1):
            candidate = proposer(best_prompt, best_train_score, tuple(history)).strip()
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

            candidate_train_score, candidate_train_report = self._evaluate_prompt(
                score_prompt, candidate
            )
            if validation_score_prompt is None:
                candidate_validation_score = candidate_train_score
                candidate_validation_report = candidate_train_report
            else:
                candidate_validation_score, candidate_validation_report = self._evaluate_prompt(
                    validation_score_prompt, candidate
                )
            accepted = candidate_validation_score > best_validation_score
            history.append(
                {
                    "iteration": iteration,
                    "score": candidate_validation_score,
                    "train_score": candidate_train_score,
                    "validation_score": candidate_validation_score,
                    "accepted": accepted,
                    "prompt": candidate,
                    "train_report": candidate_train_report,
                    "validation_report": candidate_validation_report,
                }
            )
            if accepted:
                best_prompt = candidate
                best_train_score = candidate_train_score
                best_train_report = candidate_train_report
                best_validation_score = candidate_validation_score
                best_validation_report = candidate_validation_report
            self._persist(history)

        return OptimizationResult(
            best_prompt=best_prompt,
            best_score=best_validation_score,
            history=tuple(history),
            best_train_score=best_train_score,
            best_train_report=best_train_report,
            best_validation_report=best_validation_report,
        )

    def _evaluate_prompt(
        self,
        scorer: ScorePrompt,
        prompt: str,
    ) -> tuple[float, dict[str, object] | None]:
        evaluate = getattr(scorer, "evaluate", None)
        if callable(evaluate):
            report = evaluate(prompt)
            return self._score(report.score), report.to_dict()
        return self._score(scorer(prompt)), None

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