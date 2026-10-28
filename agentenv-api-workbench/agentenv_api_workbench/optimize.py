from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .config import load_environment
from .evaluation import WorkbenchEvaluator, split_task_indices
from .fixtures import DEFAULT_TASKS
from .llm import OpenAIChatModel
from .optimizer import PromptOptimizer, propose_prompt
from .plugins import load_plugin_bundle


def _required_environment(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    expected_names = " or ".join(names)
    raise SystemExit(f"Set {expected_names} in the environment or .env file")


def resolve_state_path(state_arg: str | None, mode: str) -> Path:
    workbench_root = Path(__file__).resolve().parents[1]
    path = Path(state_arg) if state_arg else Path("runs") / f"{mode}-optimizer.json"
    return path if path.is_absolute() else workbench_root / path


def _create_model(api_key: str, model_name: str, temperature: float, optimizer: bool = False) -> OpenAIChatModel:
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    if optimizer:
        azure_endpoint = os.environ.get("OPTIMIZER_AZURE_OPENAI_ENDPOINT", azure_endpoint)
        api_version = os.environ.get("OPTIMIZER_AZURE_OPENAI_API_VERSION", api_version)

    if azure_endpoint:
        if "/openai/v1" in azure_endpoint.casefold():
            return OpenAIChatModel(
                api_key=api_key,
                model=model_name,
                azure_endpoint=azure_endpoint,
                temperature=temperature,
            )
        if not api_version:
            raise SystemExit("Set AZURE_OPENAI_API_VERSION when using Azure OpenAI")
        return OpenAIChatModel(
            api_key=api_key,
            model=model_name,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            temperature=temperature,
        )

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if optimizer:
        base_url = os.environ.get("OPTIMIZER_BASE_URL", base_url)
    return OpenAIChatModel(
        api_key=api_key,
        model=model_name,
        base_url=base_url,
        temperature=temperature,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize API plugin instructions")
    parser.add_argument("--mode", choices=("api_design", "api_documentation"), required=True)
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--server", default="http://127.0.0.1:36011")
    parser.add_argument("--state", default=None)
    args = parser.parse_args()

    if args.iterations < 0:
        raise SystemExit("--iterations cannot be negative")

    load_environment()
    plugin_root = _required_environment("AGENTGYM_PLUGINS_ROOT")
    api_key = _required_environment("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY")
    model_name = _required_environment("OPENAI_MODEL", "AZURE_OPENAI_DEPLOYMENT")
    optimizer_model_name = os.environ.get("OPTIMIZER_MODEL", model_name)

    worker = _create_model(
        api_key=api_key,
        model_name=model_name,
        temperature=0.1,
    )
    optimizer_model = _create_model(
        api_key=os.environ.get("OPTIMIZER_API_KEY", api_key),
        model_name=optimizer_model_name,
        temperature=0.7,
        optimizer=True,
    )
    initial_prompt = load_plugin_bundle(plugin_root, args.mode).prompt
    task_count = sum(task.mode == args.mode for task in DEFAULT_TASKS)
    training_indices, validation_indices = split_task_indices(task_count)
    training_evaluator = WorkbenchEvaluator(
        worker,
        args.server,
        args.mode,
        plugin_root,
        task_indices=training_indices,
    )
    validation_evaluator = WorkbenchEvaluator(
        worker,
        args.server,
        args.mode,
        plugin_root,
        task_indices=validation_indices,
    )
    state_path = resolve_state_path(args.state, args.mode)
    optimizer = PromptOptimizer(state_path)
    result = optimizer.run(
        initial_prompt=initial_prompt,
        score_prompt=training_evaluator,
        proposer=lambda prompt, score, history: propose_prompt(
            optimizer_model, prompt, score, history
        ),
        iterations=args.iterations,
        validation_score_prompt=validation_evaluator,
    )
    print(
        json.dumps(
            {
                "best_training_score": result.best_train_score,
                "best_validation_score": result.best_score,
                "training_task_indices": list(training_indices),
                "validation_task_indices": list(validation_indices),
                "best_training_report": result.best_train_report,
                "best_validation_report": result.best_validation_report,
                "iterations": len(result.history) - 1,
                "state_file": str(state_path.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()