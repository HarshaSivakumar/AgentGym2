from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal


TaskMode = Literal["api_design", "api_documentation"]
EndpointExtractor = Callable[[str], str]


@dataclass(frozen=True)
class WorkbenchTask:
    task_id: str
    mode: TaskMode
    prompt: str
    expected_terms: tuple[str, ...]
    source_code: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("api_design", "api_documentation"):
            raise ValueError(f"Unsupported task mode: {self.mode}")
        if not self.expected_terms:
            raise ValueError("Each task must define at least one expected term")
        if self.mode == "api_documentation" and not self.source_code:
            raise ValueError("Documentation tasks require source_code")


class ApiWorkbenchEnvironment:
    def __init__(
        self,
        tasks: list[WorkbenchTask],
        endpoint_extractor: EndpointExtractor | None = None,
    ) -> None:
        if not tasks:
            raise ValueError("At least one task is required")
        self._tasks = tuple(tasks)
        self._endpoint_extractor = endpoint_extractor
        self._task: WorkbenchTask | None = None
        self._observation = "Environment has not been reset."
        self._done = True

    def __len__(self) -> int:
        return len(self._tasks)

    def reset(self, task_index: int) -> dict[str, object]:
        if not 0 <= task_index < len(self._tasks):
            raise IndexError(f"Task index out of range: {task_index}")

        task = self._tasks[task_index]
        self._task = task
        self._done = False
        sections = [f"Task: {task.prompt}"]

        if task.source_code is not None:
            sections.append(f"Source code:\n```\n{task.source_code}\n```")
        if task.mode == "api_documentation" and self._endpoint_extractor is not None:
            sections.append(
                "Endpoint extraction report:\n"
                + self._endpoint_extractor(task.source_code or "")
            )

        self._observation = "\n\n".join(sections)
        return {
            "task_id": task.task_id,
            "mode": task.mode,
            "observation": self._observation,
            "reward": 0.0,
            "done": False,
        }

    def observe(self) -> dict[str, object]:
        if self._task is None:
            raise RuntimeError("Reset the environment before observing")
        return {
            "task_id": self._task.task_id,
            "mode": self._task.mode,
            "observation": self._observation,
            "reward": 0.0,
            "done": self._done,
        }

    def step(self, response: str) -> dict[str, object]:
        if self._task is None:
            raise RuntimeError("Reset the environment before stepping")
        if self._done:
            raise RuntimeError("Task is complete; reset before stepping again")
        if not isinstance(response, str) or not response.strip():
            raise ValueError("Agent response must be a non-empty string")

        normalized_response = response.casefold()
        matched_terms = [
            term
            for term in self._task.expected_terms
            if term.casefold() in normalized_response
        ]
        reward = len(matched_terms) / len(self._task.expected_terms)
        self._done = True
        self._observation = "Task complete."

        return {
            "task_id": self._task.task_id,
            "observation": self._observation,
            "reward": reward,
            "done": True,
            "info": {
                "matched_terms": matched_terms,
                "expected_terms": list(self._task.expected_terms),
            },
        }

    def close(self) -> None:
        self._task = None
        self._observation = "Environment has not been reset."
        self._done = True