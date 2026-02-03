import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSWEA_SRC = ROOT / "work" / "swebench" / "mini-swe-agent" / "src"
sys.path.insert(0, str(MSWEA_SRC))

from minisweagent.environments.local import LocalEnvironment
from minisweagent.exceptions import Submitted


class TestEmptySubmissionHandling(unittest.TestCase):
    def setUp(self):
        self.env = LocalEnvironment()

    def _assert_submission(self, output, expected_submission):
        with self.assertRaises(Submitted) as ctx:
            self.env._check_finished(output)
        message = ctx.exception.messages[0]
        self.assertEqual(message.get("extra", {}).get("submission", None), expected_submission)
        self.assertEqual(message.get("content", None), expected_submission)

    def test_empty_submission_is_allowed(self):
        output = {"output": "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n", "returncode": 0}
        self._assert_submission(output, "")

    def test_non_empty_submission_is_preserved(self):
        patch = "diff --git a/file b/file\n+change\n"
        output = {"output": f"COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n{patch}", "returncode": 0}
        self._assert_submission(output, patch)

    def test_non_matching_output_does_not_submit(self):
        output = {"output": "not a submission\n", "returncode": 0}
        self.env._check_finished(output)


if __name__ == "__main__":
    unittest.main()
