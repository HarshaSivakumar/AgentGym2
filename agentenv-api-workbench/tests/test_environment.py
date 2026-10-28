import unittest

from agentenv_api_workbench import ApiWorkbenchEnvironment, WorkbenchTask


class ApiWorkbenchEnvironmentTests(unittest.TestCase):
    def test_reset_includes_task_source_and_extracted_endpoints(self) -> None:
        task = WorkbenchTask(
            task_id="docs-1",
            mode="api_documentation",
            prompt="Document the routes in the source.",
            expected_terms=("GET /health",),
            source_code="app.get('/health', handler)",
        )
        environment = ApiWorkbenchEnvironment(
            [task], endpoint_extractor=lambda source: f"Extracted from: {source}"
        )

        result = environment.reset(0)

        self.assertIn("Task: Document the routes", result["observation"])
        self.assertIn("app.get('/health', handler)", result["observation"])
        self.assertIn("Extracted from: app.get('/health', handler)", result["observation"])
        self.assertFalse(result["done"])

    def test_step_scores_expected_terms_case_insensitively(self) -> None:
        task = WorkbenchTask(
            task_id="design-1",
            mode="api_design",
            prompt="Define a health endpoint.",
            expected_terms=("HealthResponse", "status"),
        )
        environment = ApiWorkbenchEnvironment([task])
        environment.reset(0)

        result = environment.step("type HealthResponse = { STATUS: 'ok' }")

        self.assertEqual(result["reward"], 1.0)
        self.assertTrue(result["done"])
        self.assertEqual(result["info"]["matched_terms"], ["HealthResponse", "status"])

    def test_step_requires_reset_and_rejects_steps_after_completion(self) -> None:
        task = WorkbenchTask(
            task_id="design-1",
            mode="api_design",
            prompt="Define a health endpoint.",
            expected_terms=("HealthResponse",),
        )
        environment = ApiWorkbenchEnvironment([task])

        with self.assertRaises(RuntimeError):
            environment.step("HealthResponse")

        environment.reset(0)
        environment.step("HealthResponse")
        with self.assertRaises(RuntimeError):
            environment.step("HealthResponse")


if __name__ == "__main__":
    unittest.main()