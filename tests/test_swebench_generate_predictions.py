import json
import os
import tempfile
import unittest

from scripts.swebench_generate_predictions import (
    append_jsonl,
    build_user_prompt,
    parse_csv_list,
    read_existing_live_predictions,
    read_existing_swebench_predictions,
    sanitize_patch,
    write_live_predictions,
)


class TestSWEbenchGeneratePredictions(unittest.TestCase):
    def test_build_user_prompt_includes_hints(self):
        instance = {
            "repo": "repo/name",
            "instance_id": "repo__name-123",
            "problem_statement": "Fix the bug",
            "hints_text": "Use existing helper",
        }
        prompt = build_user_prompt(instance)
        self.assertIn("Repository: repo/name", prompt)
        self.assertIn("Instance ID: repo__name-123", prompt)
        self.assertIn("Problem Statement:", prompt)
        self.assertIn("Fix the bug", prompt)
        self.assertIn("Hints:", prompt)
        self.assertIn("Use existing helper", prompt)

    def test_parse_csv_list(self):
        self.assertEqual(parse_csv_list("a, b, c"), ["a", "b", "c"])
        self.assertEqual(parse_csv_list(""), [])
        self.assertEqual(parse_csv_list(None), [])

    def test_read_existing_swebench_predictions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "predictions.jsonl")
            append_jsonl(path, {"instance_id": "a", "model_patch": "x"})
            append_jsonl(path, {"instance_id": "b", "model_patch": "y"})
            instance_ids = read_existing_swebench_predictions(path)
            self.assertEqual(instance_ids, {"a", "b"})

    def test_read_existing_live_predictions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "predictions.json")
            payload = {"a": {"model_patch": "x"}}
            write_live_predictions(path, payload)
            loaded = read_existing_live_predictions(path)
            self.assertEqual(loaded, payload)

    def test_write_live_predictions_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "predictions.json")
            payload = {"a": {"model_patch": "x"}, "b": {"model_patch": "y"}}
            write_live_predictions(path, payload)
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertEqual(data, payload)

    def test_sanitize_patch_strips_fences(self):
        raw = "```diff\n--- a/foo.py\n+++ b/foo.py\n@@\n-1\n+2\n```\n"
        sanitized = sanitize_patch(raw)
        self.assertEqual(sanitized, "--- a/foo.py\n+++ b/foo.py\n@@\n-1\n+2\n")

    def test_sanitize_patch_handles_empty(self):
        self.assertEqual(sanitize_patch(""), "")
        self.assertEqual(sanitize_patch("   \n"), "")


if __name__ == "__main__":
    unittest.main()
