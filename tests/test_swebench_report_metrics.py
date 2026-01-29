import json
import os
import tempfile
import unittest

from scripts.swebench_report_metrics import (
    calculate_live_metrics,
    calculate_swebench_metrics,
    render_markdown,
)


class TestSWEbenchReportMetrics(unittest.TestCase):
    def test_calculate_swebench_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "report.json")
            payload = {
                "total_instances": 10,
                "resolved_instances": 4,
                "error_instances": 2,
            }
            with open(report_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            metrics = calculate_swebench_metrics(report_path)
            self.assertEqual(metrics["total_tasks"], 10)
            self.assertEqual(metrics["solved"], 4)
            self.assertAlmostEqual(metrics["pass_rate"], 0.4)
            self.assertEqual(metrics["errors"], 2)

    def test_calculate_live_metrics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for split, success, failure, error in [("c", 2, 3, 1), ("cpp", 1, 1, 0)]:
                split_dir = os.path.join(tmpdir, split)
                os.makedirs(split_dir, exist_ok=True)
                with open(os.path.join(split_dir, "results.json"), "w", encoding="utf-8") as handle:
                    json.dump(
                        {"success": success, "failure": failure, "error": error},
                        handle,
                    )
            metrics = calculate_live_metrics(tmpdir, ["c", "cpp"])
            self.assertEqual(metrics["total_tasks"], 8)
            self.assertEqual(metrics["solved"], 3)
            self.assertEqual(metrics["errors"], 1)
            self.assertAlmostEqual(metrics["pass_rate"], 3 / 8)
            self.assertIn("c", metrics["splits"])
            self.assertIn("cpp", metrics["splits"])

    def test_render_markdown(self):
        metrics = {
            "model": "demo-model",
            "swebench_multilingual": {
                "total_tasks": 10,
                "solved": 5,
                "pass_rate": 0.5,
                "errors": 0,
            },
            "swebench_live_multilang": {
                "total_tasks": 4,
                "solved": 1,
                "pass_rate": 0.25,
                "errors": 1,
                "splits": {
                    "c": {"total_tasks": 2, "solved": 1, "pass_rate": 0.5, "errors": 0},
                    "cpp": {"total_tasks": 2, "solved": 0, "pass_rate": 0.0, "errors": 1},
                },
            },
        }
        output = render_markdown(metrics)
        self.assertIn("Model: demo-model", output)
        self.assertIn("SWE-bench Multilingual:", output)
        self.assertIn("SWE-bench-Live MultiLang:", output)
        self.assertIn("- c:", output)
        self.assertIn("- cpp:", output)


if __name__ == "__main__":
    unittest.main()
