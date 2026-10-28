from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Literal

from .environment import ApiWorkbenchEnvironment
from .extractor import NodeEndpointExtractor
from .fixtures import DEFAULT_TASKS


AgentMode = Literal["api_design", "api_documentation"]


@dataclass
class _Session:
    environment: ApiWorkbenchEnvironment
    lock: threading.Lock


class ApiWorkbenchManager:
    def __init__(self, endpoint_extractor: NodeEndpointExtractor | None = None) -> None:
        self._endpoint_extractor = endpoint_extractor
        self._next_id = 0
        self._sessions: dict[int, _Session] = {}
        self._lock = threading.Lock()

    def create(self, agent_mode: AgentMode) -> dict[str, int | str]:
        tasks = [task for task in DEFAULT_TASKS if task.mode == agent_mode]
        if not tasks:
            raise ValueError(f"No tasks configured for mode: {agent_mode}")
        environment = ApiWorkbenchEnvironment(tasks, self._endpoint_extractor)
        with self._lock:
            session_id = self._next_id
            self._next_id += 1
            self._sessions[session_id] = _Session(environment, threading.Lock())
        return {"id": session_id, "data_len": len(environment), "agent_mode": agent_mode}

    def _session(self, session_id: int) -> _Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown environment id: {session_id}")
        return session

    def reset(self, session_id: int, data_idx: int) -> dict[str, object]:
        session = self._session(session_id)
        with session.lock:
            return session.environment.reset(data_idx)

    def observe(self, session_id: int) -> dict[str, object]:
        session = self._session(session_id)
        with session.lock:
            return session.environment.observe()

    def step(self, session_id: int, action: str) -> dict[str, object]:
        session = self._session(session_id)
        with session.lock:
            return session.environment.step(action)

    def close(self, session_id: int) -> dict[str, bool]:
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            return {"closed": False}
        with session.lock:
            session.environment.close()
        return {"closed": True}