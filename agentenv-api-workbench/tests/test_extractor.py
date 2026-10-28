import tempfile
import unittest
from pathlib import Path

from agentenv_api_workbench import NodeEndpointExtractor


class NodeEndpointExtractorTests(unittest.TestCase):
    def test_runs_script_with_source_in_a_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "extract.js"
            script_path.write_text(
                "import fs from 'fs';\n"
                "console.log(fs.readFileSync(process.argv[2], 'utf8'));\n",
                encoding="utf-8",
            )
            extractor = NodeEndpointExtractor(script_path)

            report = extractor("app.get('/health', handler);\n")

        self.assertEqual(report, "app.get('/health', handler);")

    def test_rejects_missing_extractor_script(self) -> None:
        extractor = NodeEndpointExtractor(Path("missing-endpoint-extractor.js"))

        with self.assertRaises(FileNotFoundError):
            extractor("app.get('/health', handler);")


if __name__ == "__main__":
    unittest.main()