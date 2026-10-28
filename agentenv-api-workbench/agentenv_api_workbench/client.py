from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests.exceptions import RequestException

from .plugins import load_plugin_bundle


@dataclass(frozen=True)
class StepOutput:
    state: str
    reward: float
    done: bool


class ApiWorkbenchEnvClient:
    def __init__(
        self,
        env_server_base: str,
        agent_mode: str,
        plugin_root: str,
        prompt_override: str | None = None,
        timeout: float = 30,
    ) -> None:
        self.env_server_base = env_server_base.rstrip("/")
        self.agent_mode = agent_mode
        self.timeout = timeout
        self.bundle = load_plugin_bundle(plugin_root, agent_mode)
        self.info: dict[str, Any] = {}

        response = requests.post(
            f"{self.env_server_base}/create",
            json={"agent_mode": agent_mode},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise RequestException(f"Failed to create API workbench session: {response.text}")
        payload = response.json()
        self.env_id = payload["id"]
        self.data_len = payload["data_len"]

        prompt = prompt_override or self.bundle.prompt
        if agent_mode == "api_documentation":
            prompt += (
                "\n\nThe host runs endpoint_extractor on the supplied fixture before "
                "your turn. Its report is included in the observation; use it as "
                "the tool result."
            )
        self.system_prompt = prompt

    def __len__(self) -> int:
        return self.data_len

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {"id": self.env_id, **data}
        response = requests.post(
            f"{self.env_server_base}/{path}", json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def _get(self, path: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.env_server_base}/{path}",
            params={"id": self.env_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def observe(self) -> str:
        if "observation" in self.info:
            return str(self.info["observation"])
        return str(self._get("observation")["observation"])

    def step(self, action: str) -> StepOutput:
        response = self._post("step", {"action": action})
        self.info = response
        return StepOutput(
            state=str(response["observation"]),
            reward=float(response["reward"]),
            done=bool(response["done"]),
        )

    def reset(self, idx: int) -> dict[str, Any]:
        response = self._post("reset", {"data_idx": idx})
        self.info = response
        return response

    def close(self) -> dict[str, Any]:
        return self._post("close", {})