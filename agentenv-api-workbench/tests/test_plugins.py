import tempfile
import unittest
from pathlib import Path

from agentenv_api_workbench.plugins import load_plugin_bundle


class PluginBundleTests(unittest.TestCase):
    def test_loads_agent_and_skill_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "API-First-Code-Architect"
            agent = plugin_dir / "agents" / "API-First-Code-Architect.agent.md"
            agent.parent.mkdir(parents=True)
            agent.write_text("agent instructions", encoding="utf-8")
            skill_names = (
                "contract-first-types",
                "validation-schema-designer",
                "error-modeler",
                "guarded-skeleton-implementations",
            )
            for skill_name in skill_names:
                skill = plugin_dir / "skills" / skill_name / "skill.md"
                skill.parent.mkdir(parents=True)
                skill.write_text(f"{skill_name} instructions", encoding="utf-8")

            bundle = load_plugin_bundle(temp_dir, "api_design")

        self.assertEqual(bundle.agent_name, "API-First-Code-Architect")
        self.assertIn("agent instructions", bundle.prompt)
        self.assertIn("contract-first-types instructions", bundle.prompt)
        self.assertIn("guarded-skeleton-implementations instructions", bundle.prompt)


if __name__ == "__main__":
    unittest.main()