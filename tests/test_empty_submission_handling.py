import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MSWEA_SRC = ROOT / "work" / "swebench" / "mini-swe-agent" / "src"
sys.path.insert(0, str(MSWEA_SRC))

from minisweagent.agents.default import AgentConfig, DefaultAgent, EmptySubmissionError, Submitted


class DummyModel:
    def __init__(self):
        self.n_calls = 0
        self.cost = 0.0

    def get_template_vars(self):
        return {}


class DummyEnv:
    def get_template_vars(self):
        return {}


class TestEmptySubmissionHandling(unittest.TestCase):
    def setUp(self):
        config = AgentConfig(
            system_template="",
            instance_template="",
            timeout_template="",
            format_error_template="",
            action_observation_template="",
        )
        self.agent = DefaultAgent(DummyModel(), DummyEnv(), **config.model_dump())

    def test_empty_submission_raises(self):
        output = {"output": "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n"}
        with self.assertRaises(EmptySubmissionError):
            self.agent.has_finished(output)

    def test_non_empty_submission_passes(self):
        patch = "diff --git a/file b/file\n+change\n"
        output = {"output": f"COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT\n{patch}"}
        with self.assertRaises(Submitted) as ctx:
            self.agent.has_finished(output)
        self.assertIn(patch, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
