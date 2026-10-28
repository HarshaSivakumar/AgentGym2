from __future__ import annotations

from statistics import mean
from typing import Protocol

from .client import ApiWorkbenchEnvClient


class ChatModel(Protocol):
    def generate(self, conversation: list[dict[str, str]]) -> tuple[str, str | None]: ...


class WorkbenchEvaluator:
    def __init__(
        self,
        agent: ChatModel,
        env_server_base: str,
        agent_mode: str,
        plugin_root: str,
    ) -> None:
        self.agent = agent
        self.env_server_base = env_server_base
        self.agent_mode = agent_mode
        self.plugin_root = plugin_root

    def __call__(self, prompt: str) -> float:
        client = ApiWorkbenchEnvClient(
            env_server_base=self.env_server_base,
            agent_mode=self.agent_mode,
            plugin_root=self.plugin_root,
            prompt_override=prompt,
        )
        try:
            rewards = []
            for task_index in range(len(client)):
                initial = client.reset(task_index)
                conversation = [
                    {"role": "system", "content": client.system_prompt},
                    {"role": "user", "content": str(initial["observation"])},
                ]
                response, _ = self.agent.generate(conversation)
                rewards.append(client.step(response).reward)
            if not rewards:
                raise RuntimeError("The workbench returned no evaluation experiences")
            return mean(rewards)
        finally:
            client.close()