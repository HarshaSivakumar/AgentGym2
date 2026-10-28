from __future__ import annotations

from typing import Any, Mapping

from agentenv.controller import BaseEnvClient, BaseTask
from agentenv.controller.types import ConversationMessage, StepOutput

from .client import ApiWorkbenchEnvClient


class AgentGymApiWorkbenchEnvClient(BaseEnvClient):
    def __init__(
        self,
        env_server_base: str,
        agent_mode: str,
        plugin_root: str,
        prompt_override: str | None = None,
        timeout: float = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._client = ApiWorkbenchEnvClient(
            env_server_base=env_server_base,
            agent_mode=agent_mode,
            plugin_root=plugin_root,
            prompt_override=prompt_override,
            timeout=timeout,
        )
        self.conversation_start = (
            ConversationMessage(
                {"from": "human", "loss": None, "value": self._client.system_prompt}
            ),
            ConversationMessage({"from": "gpt", "loss": False, "value": "Ready."}),
        )

    def __len__(self) -> int:
        return len(self._client)

    def observe(self) -> str:
        return self._client.observe()

    def step(self, action: str) -> StepOutput:
        return self._client.step(action)

    def reset(self, idx: int) -> dict[str, Any]:
        return self._client.reset(idx)

    def close(self) -> dict[str, Any]:
        return self._client.close()


class AgentGymApiWorkbenchTask(BaseTask):
    env_client_cls = AgentGymApiWorkbenchEnvClient
    env_name = "APIWorkbench"

    def __init__(
        self,
        client_args: Mapping[str, Any],
        n_clients: int = 1,
    ) -> None:
        super().__init__(client_args=client_args, n_clients=n_clients)