# AgentGym API Workbench

This custom environment evaluates two instruction-based plugins using synthetic tasks:

- `API-First-Code-Architect` designs TypeScript API contracts and guarded skeletons.
- `API-Documentation-Generator` documents routes from fixture source using its existing Node.js endpoint extractor.

The plugin Markdown is read from disk and is not modified. The environment does not run inside VS Code Copilot. It uses AgentGym's `BaseTask`/`BaseEnvClient` interface and an OpenAI-compatible chat model for worker and optimizer calls. The optimizer revises prompts between fixed evaluation runs; it does not train model weights.

## Install

From PowerShell in this directory, install the runtime dependencies:

```powershell
python -m pip install "fastapi>=0.110" "requests>=2.31" "uvicorn>=0.27" "openai>=1.30"
```

This installs the workbench server and OpenAI-compatible client only. It does not install AgentGym's training stack. Node.js must be available on `PATH` for endpoint extraction.

The optional `agentgym_adapter.py` provides `BaseTask`/`BaseEnvClient` integration when AgentGym is already installed. Importing the standalone optimizer does not require that adapter or the core package.

## Configure And Launch

Set the plugin collection root, which contains both plugin folders:

```powershell
$env:AGENTGYM_PLUGINS_ROOT = "C:\path\to\Plugins"
python -m agentenv_api_workbench.launch --host 127.0.0.1 --port 36011
```

For a classic Azure OpenAI resource, use the deployment name as `OPENAI_MODEL`, with the resource endpoint and API version. For an Azure AI Foundry OpenAI v1 endpoint ending in `/openai/v1/responses`, set that full URL as `AZURE_OPENAI_ENDPOINT`; the workbench uses the Responses API and does not need `AZURE_OPENAI_API_VERSION`. Do not commit credentials or paste them into chat.

For the OpenAI v1 Responses endpoint, set `OPENAI_MODEL` to the deployed model name (for example, `gpt-5.4-mini`). A model catalog version such as `2026-03-17` is not an API version and should not be placed in `AZURE_OPENAI_API_VERSION`.

```powershell
$env:OPENAI_API_KEY = "<your-key>"
$env:OPENAI_MODEL = "<your-deployment-or-model-name>"
$env:AZURE_OPENAI_ENDPOINT = "https://<resource-name>.services.ai.azure.com/openai/v1/responses"
python -m agentenv_api_workbench.optimize --mode api_design --iterations 2
```

Run the command in the second PowerShell terminal after starting the server. Use `--mode api_documentation` to evaluate the documentation plugin. The optimizer reuses the Azure endpoint and key by default; `OPTIMIZER_MODEL`, `OPTIMIZER_API_KEY`, and `OPTIMIZER_AZURE_OPENAI_ENDPOINT` can override them. For classic Azure OpenAI, also set `AZURE_OPENAI_API_VERSION`; the optimizer can override it with `OPTIMIZER_AZURE_OPENAI_API_VERSION`. For non-Azure OpenAI-compatible services, set `OPENAI_BASE_URL` instead; `OPTIMIZER_BASE_URL` can override the optimizer endpoint.

Optimization history, candidate prompts, and scores are written to `runs/api-workbench-optimizer.json`. A candidate replaces the current best only when its score improves on the same fixed task set.

## Environment API

- `GET /tasks` lists the synthetic task IDs and modes.
- `POST /create` with `{"agent_mode":"api_design"}` or `{"agent_mode":"api_documentation"}` creates an isolated session.
- `POST /reset` with `{"id":0,"data_idx":0}` loads a task.
- `GET /observation?id=0` returns the current task state.
- `POST /step` with `{"id":0,"action":"..."}` scores a response and completes the task.
- `POST /close` with `{"id":0}` releases the session.

The initial reward is the fraction of required terms present in the response. This is a lightweight baseline rubric, not a semantic quality score. The endpoint extractor uses regex patterns, so it may miss unsupported or multiline route declarations. Initial tasks contain fixture code only; arbitrary repository paths are not accepted.

## Tests

From the repository root:

```powershell
python -c "import sys, unittest; sys.path.insert(0, r'agentenv-api-workbench'); suite = unittest.defaultTestLoader.discover(r'agentenv-api-workbench/tests'); result = unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())"
```