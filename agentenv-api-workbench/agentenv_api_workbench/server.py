from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .extractor import NodeEndpointExtractor
from .fixtures import DEFAULT_TASKS
from .manager import ApiWorkbenchManager


class CreateRequest(BaseModel):
    agent_mode: Literal["api_design", "api_documentation"]


class ResetRequest(BaseModel):
    id: int
    data_idx: int


class ActionRequest(BaseModel):
    id: int
    action: str


class IdRequest(BaseModel):
    id: int


def _configured_extractor() -> NodeEndpointExtractor | None:
    plugins_root = os.environ.get("AGENTGYM_PLUGINS_ROOT")
    if not plugins_root:
        return None
    script_path = (
        Path(plugins_root)
        / "API-Documentation-Generator"
        / "scripts"
        / "endpoint_extractor.js"
    )
    return NodeEndpointExtractor(script_path)


manager = ApiWorkbenchManager(_configured_extractor())
app = FastAPI(title="AgentGym API Workbench")


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentgym-api-workbench"}


@app.get("/tasks")
def list_tasks() -> list[dict[str, str]]:
    return [{"task_id": task.task_id, "mode": task.mode} for task in DEFAULT_TASKS]


@app.post("/create")
def create_environment(body: CreateRequest) -> dict[str, int | str]:
    return manager.create(body.agent_mode)


@app.post("/reset")
def reset_environment(body: ResetRequest) -> dict[str, object]:
    try:
        return manager.reset(body.id, body.data_idx)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (IndexError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/observation")
def get_observation(id: int) -> dict[str, object]:
    try:
        return manager.observe(id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/step")
def step_environment(body: ActionRequest) -> dict[str, object]:
    try:
        return manager.step(body.id, body.action)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/close")
def close_environment(body: IdRequest) -> dict[str, bool]:
    return manager.close(body.id)