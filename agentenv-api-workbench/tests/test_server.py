import unittest

from agentenv_api_workbench.manager import ApiWorkbenchManager


class ApiWorkbenchManagerTests(unittest.TestCase):
    def test_sessions_are_isolated_and_lifecycle_is_enforced(self) -> None:
        manager = ApiWorkbenchManager(endpoint_extractor=lambda source: "Found: GET /health")
        design_session = manager.create("api_design")
        docs_session = manager.create("api_documentation")

        design_state = manager.reset(design_session["id"], 0)
        docs_state = manager.reset(docs_session["id"], 0)
        self.assertIn("Design a TypeScript POST", design_state["observation"])
        self.assertIn("Found: GET /health", docs_state["observation"])
        self.assertNotEqual(design_session["id"], docs_session["id"])

        result = manager.step(
            docs_session["id"],
            "GET /health POST /bookings Request Payload / Params Expected Response (Success)",
        )
        self.assertEqual(result["reward"], 1.0)
        self.assertTrue(result["done"])

        with self.assertRaises(RuntimeError):
            manager.step(docs_session["id"], "another response")
        self.assertEqual(manager.close(docs_session["id"]), {"closed": True})
        self.assertEqual(manager.close(docs_session["id"]), {"closed": False})


if __name__ == "__main__":
    unittest.main()