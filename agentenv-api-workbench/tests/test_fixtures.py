import unittest
from collections import Counter

from agentenv_api_workbench.fixtures import DEFAULT_TASKS


class DefaultFixtureTests(unittest.TestCase):
    def test_benchmark_has_three_tasks_per_plugin_mode(self) -> None:
        counts = Counter(task.mode for task in DEFAULT_TASKS)

        self.assertEqual(counts, {"api_design": 3, "api_documentation": 3})

    def test_each_task_has_unique_id_and_weighted_checks(self) -> None:
        task_ids = [task.task_id for task in DEFAULT_TASKS]

        self.assertEqual(len(task_ids), len(set(task_ids)))
        self.assertTrue(all(task.rubric for task in DEFAULT_TASKS))

    def test_documentation_tasks_have_source_fixtures(self) -> None:
        documentation_tasks = [
            task for task in DEFAULT_TASKS if task.mode == "api_documentation"
        ]

        self.assertTrue(all(task.source_code for task in documentation_tasks))


if __name__ == "__main__":
    unittest.main()