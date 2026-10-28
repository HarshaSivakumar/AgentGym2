from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Protocol, Sequence

from .client import ApiWorkbenchEnvClient


class ChatModel(Protocol):
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, str | None]: ...


@dataclass(frozen=True)
class TaskEvaluation:
    task_id: str
    score: float
    response: str
    passed_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    matched_terms: tuple[str, ...]
    expected_terms: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    task_results: tuple[TaskEvaluation, ...]
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "task_results": [asdict(result) for result in self.task_results],
        }


def split_task_indices(task_count: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if task_count < 2:
        raise ValueError("At least two tasks are required for a train/validation split")
    return tuple(range(task_count - 1)), (task_count - 1,)


class WorkbenchEvaluator:
    def __init__(
        self,
        agent: ChatModel,
        env_server_base: str,
        agent_mode: str,
        plugin_root: str,
        task_indices: Sequence[int] | None = None,
    ) -> None:
        self.agent = agent
        self.env_server_base = env_server_base
        self.agent_mode = agent_mode
        self.plugin_root = plugin_root
        self.task_indices = tuple(task_indices) if task_indices is not None else None

    def evaluate(self, prompt: str) -> EvaluationReport:
        client = ApiWorkbenchEnvClient(
            env_server_base=self.env_server_base,
            agent_mode=self.agent_mode,
            plugin_root=self.plugin_root,
            prompt_override=prompt,
        )
        try:
            task_indices = self.task_indices or tuple(range(len(client)))
            if not task_indices:
                raise ValueError("At least one task index is required")
            if any(index < 0 or index >= len(client) for index in task_indices):
                raise IndexError("Evaluation task index is outside the configured task set")

            task_results = []
            for task_index in task_indices:
                initial = client.reset(task_index)
                conversation = [
                    {"role": "system", "content": client.system_prompt},
                    {"role": "user", "content": str(initial["observation"])},
                ]
                response, _ = self.agent.generate(conversation)
                step_output = client.step(response)
                info = client.info.get("info", {})
                task_results.append(
                    TaskEvaluation(
                        task_id=str(initial.get("task_id", task_index)),
                        score=step_output.reward,
                        response=response,
                        passed_checks=tuple(info.get("passed_checks", ())),
                        failed_checks=tuple(info.get("failed_checks", ())),
                        matched_terms=tuple(info.get("matched_terms", ())),
                        expected_terms=tuple(info.get("expected_terms", ())),
                    )
                )
            return EvaluationReport(
                task_results=tuple(task_results),
                score=mean(result.score for result in task_results),
            )
        finally:
            client.close()

    def __call__(self, prompt: str) -> float:
        return self.evaluate(prompt).score