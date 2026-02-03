"""Tests for mini-swe-agent litellm_model tool-calling behavior.

These are unit tests that stub litellm.completion to avoid requiring a live
vLLM server.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

# Add mini-swe-agent to path
REPO_ROOT = Path(__file__).resolve().parents[1]
MINI_SWE_AGENT_SRC = REPO_ROOT / "work" / "swebench" / "mini-swe-agent" / "src"
if MINI_SWE_AGENT_SRC.exists():
    sys.path.insert(0, str(MINI_SWE_AGENT_SRC))
else:
    raise unittest.SkipTest(f"mini-swe-agent not found at {MINI_SWE_AGENT_SRC}")

from minisweagent.exceptions import FormatError
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.actions_toolcall import BASH_TOOL


class FakeFunction:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class FakeToolCall:
    def __init__(self, name: str, arguments: str, call_id: str = "call_1"):
        self.function = FakeFunction(name, arguments)
        self.id = call_id


class FakeMessage:
    def __init__(self, content: str, tool_calls):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self):
        return {"role": "assistant", "content": self.content, "tool_calls": self.tool_calls}


class FakeResponse:
    def __init__(self, message: FakeMessage):
        self.choices = [SimpleNamespace(message=message)]

    def model_dump(self):
        return {"choices": [{"message": self.choices[0].message.model_dump()}], "model": "fake-model"}


class TestLitellmToolCalling(unittest.TestCase):
    def _model(self):
        return LitellmModel(
            model_name="test-model",
            model_kwargs={"api_base": "http://localhost:8000/v1"},
            cost_tracking="ignore_errors",
        )

    @patch("minisweagent.models.litellm_model.litellm.cost_calculator.completion_cost", return_value=0.01)
    @patch("minisweagent.models.litellm_model.litellm.completion")
    def test_query_returns_actions_and_extra(self, mock_completion, _mock_cost):
        tool_calls = [FakeToolCall("bash", '{"command": "echo hi"}', "call_123")]
        response = FakeResponse(FakeMessage("ok", tool_calls))
        mock_completion.return_value = response

        model = self._model()
        result = model.query([
            {"role": "user", "content": "run a command", "extra": {"ignored": True}},
        ])

        self.assertEqual(result["content"], "ok")
        self.assertIn("extra", result)
        self.assertEqual(
            result["extra"]["actions"],
            [{"command": "echo hi", "tool_call_id": "call_123"}],
        )
        self.assertEqual(result["extra"]["response"]["model"], "fake-model")

        _, kwargs = mock_completion.call_args
        self.assertEqual(kwargs["tools"], [BASH_TOOL])
        self.assertNotIn("extra", kwargs["messages"][0])

    @patch("minisweagent.models.litellm_model.litellm.completion")
    def test_query_requires_tool_calls(self, mock_completion):
        response = FakeResponse(FakeMessage("no tools", None))
        mock_completion.return_value = response

        model = self._model()
        with self.assertRaises(FormatError):
            model.query([{"role": "user", "content": "hi"}])

    @patch("minisweagent.models.litellm_model.litellm.completion")
    def test_query_rejects_unknown_tool(self, mock_completion):
        tool_calls = [FakeToolCall("python", '{"command": "print(1)"}', "call_456")]
        response = FakeResponse(FakeMessage("bad tool", tool_calls))
        mock_completion.return_value = response

        model = self._model()
        with self.assertRaises(FormatError):
            model.query([{"role": "user", "content": "hi"}])


if __name__ == "__main__":
    unittest.main()
