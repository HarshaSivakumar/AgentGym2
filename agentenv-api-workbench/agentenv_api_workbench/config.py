from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_environment(env_file: Path | None = None) -> None:
    path = env_file or Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=path, override=False)