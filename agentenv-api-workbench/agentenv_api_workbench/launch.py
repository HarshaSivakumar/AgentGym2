from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the AgentGym API Workbench")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=36011)
    args = parser.parse_args()
    uvicorn.run("agentenv_api_workbench.server:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()