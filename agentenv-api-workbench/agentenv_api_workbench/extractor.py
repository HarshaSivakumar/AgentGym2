from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


class NodeEndpointExtractor:
    def __init__(
        self,
        script_path: str | Path,
        node_executable: str = "node",
        timeout_seconds: float = 10,
    ) -> None:
        self.script_path = Path(script_path).resolve()
        self.node_executable = node_executable
        self.timeout_seconds = timeout_seconds
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def __call__(self, source_code: str) -> str:
        if not self.script_path.is_file():
            raise FileNotFoundError(f"Endpoint extractor not found: {self.script_path}")

        with tempfile.TemporaryDirectory(prefix="agentgym-api-workbench-") as temp_dir:
            source_path = Path(temp_dir) / "fixture.js"
            source_path.write_text(source_code, encoding="utf-8")
            result = subprocess.run(
                [self.node_executable, str(self.script_path), str(source_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )

        if result.returncode != 0:
            message = result.stderr.strip() or "Endpoint extractor exited unsuccessfully"
            raise RuntimeError(message)
        return result.stdout.strip()