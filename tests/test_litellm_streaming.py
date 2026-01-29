"""Tests for mini-swe-agent litellm_model streaming functionality.

These tests verify that the streaming mode fix works correctly to avoid
HTTP read timeouts on long vLLM generations.

Requires: vLLM running at http://localhost:8000/v1
"""

import os
import sys
import unittest
from pathlib import Path

# Add mini-swe-agent to path
REPO_ROOT = Path(__file__).resolve().parents[1]
MINI_SWE_AGENT_SRC = REPO_ROOT / "work" / "swebench" / "mini-swe-agent" / "src"
if MINI_SWE_AGENT_SRC.exists():
    sys.path.insert(0, str(MINI_SWE_AGENT_SRC))
else:
    raise unittest.SkipTest(f"mini-swe-agent not found at {MINI_SWE_AGENT_SRC}")

from minisweagent.models.litellm_model import LitellmModel, LitellmModelConfig


# Skip tests if vLLM is not running
def vllm_available():
    """Check if vLLM is running at localhost:8000."""
    try:
        import requests
        response = requests.get("http://localhost:8000/v1/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@unittest.skipUnless(vllm_available(), "vLLM not running at localhost:8000")
class TestLitellmStreaming(unittest.TestCase):
    """Test streaming mode for litellm model."""

    def setUp(self):
        """Set up test model with vLLM."""
        self.model_name = "hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
        self.api_base = "http://localhost:8000/v1"

    def test_streaming_produces_content(self):
        """Streaming mode should produce non-empty content."""
        model = LitellmModel(
            model_name=self.model_name,
            model_kwargs={"api_base": self.api_base, "max_tokens": 50},
            cost_tracking="ignore_errors",
            use_streaming=True,
        )

        result = model.query([{"role": "user", "content": "Say hello in exactly 5 words."}])

        self.assertIn("content", result)
        self.assertIsInstance(result["content"], str)
        self.assertGreater(len(result["content"]), 0)
        print(f"Streaming content: {result['content']!r}")

    def test_streaming_response_has_extra(self):
        """Streaming response should include extra metadata."""
        model = LitellmModel(
            model_name=self.model_name,
            model_kwargs={"api_base": self.api_base, "max_tokens": 20},
            cost_tracking="ignore_errors",
            use_streaming=True,
        )

        result = model.query([{"role": "user", "content": "Hi"}])

        self.assertIn("extra", result)
        self.assertIn("response", result["extra"])
        # Response should have model_dump() result
        response_data = result["extra"]["response"]
        self.assertIn("choices", response_data)
        self.assertIn("model", response_data)

    def test_non_streaming_still_works(self):
        """Non-streaming mode should still work when disabled."""
        model = LitellmModel(
            model_name=self.model_name,
            model_kwargs={"api_base": self.api_base, "max_tokens": 20},
            cost_tracking="ignore_errors",
            use_streaming=False,
        )

        result = model.query([{"role": "user", "content": "Hi"}])

        self.assertIn("content", result)
        self.assertIsInstance(result["content"], str)
        self.assertGreater(len(result["content"]), 0)
        print(f"Non-streaming content: {result['content']!r}")

    def test_streaming_matches_non_streaming_format(self):
        """Streaming and non-streaming should produce same result format."""
        messages = [{"role": "user", "content": "What is 2+2? Answer with just the number."}]

        streaming_model = LitellmModel(
            model_name=self.model_name,
            model_kwargs={"api_base": self.api_base, "max_tokens": 10, "temperature": 0},
            cost_tracking="ignore_errors",
            use_streaming=True,
        )
        non_streaming_model = LitellmModel(
            model_name=self.model_name,
            model_kwargs={"api_base": self.api_base, "max_tokens": 10, "temperature": 0},
            cost_tracking="ignore_errors",
            use_streaming=False,
        )

        streaming_result = streaming_model.query(messages)
        non_streaming_result = non_streaming_model.query(messages)

        # Both should have same keys
        self.assertEqual(set(streaming_result.keys()), set(non_streaming_result.keys()))

        # Both should have content
        self.assertIn("content", streaming_result)
        self.assertIn("content", non_streaming_result)

        # Content should be similar (may not be identical due to sampling)
        print(f"Streaming: {streaming_result['content']!r}")
        print(f"Non-streaming: {non_streaming_result['content']!r}")

    def test_streaming_default_enabled(self):
        """Streaming should be enabled by default."""
        config = LitellmModelConfig(
            model_name="test-model",
            cost_tracking="ignore_errors",
        )
        self.assertTrue(config.use_streaming)

    def test_streaming_env_var_disable(self):
        """MSWEA_USE_STREAMING=false should disable streaming."""
        original = os.environ.get("MSWEA_USE_STREAMING")
        try:
            os.environ["MSWEA_USE_STREAMING"] = "false"
            # Need to reimport to pick up env var
            from importlib import reload
            import minisweagent.models.litellm_model as lm
            reload(lm)
            config = lm.LitellmModelConfig(
                model_name="test-model",
                cost_tracking="ignore_errors",
            )
            self.assertFalse(config.use_streaming)
        finally:
            # Restore original
            if original is None:
                os.environ.pop("MSWEA_USE_STREAMING", None)
            else:
                os.environ["MSWEA_USE_STREAMING"] = original
            # Reload to restore default
            reload(lm)


class TestStreamingResponseReconstruction(unittest.TestCase):
    """Test the response reconstruction logic without requiring vLLM."""

    def test_reconstruct_handles_empty_stream(self):
        """Should handle edge case of empty stream."""
        from litellm.types.utils import Choices, Message, ModelResponse, Usage

        model = LitellmModel(
            model_name="test-model",
            cost_tracking="ignore_errors",
            use_streaming=True,
        )

        # Simulate empty stream
        empty_stream = iter([])

        # This should not crash, but return empty content
        # We need to handle the case where last_chunk is None
        result = model._reconstruct_response_from_stream(empty_stream)

        self.assertEqual(result.choices[0].message.content, "")


if __name__ == "__main__":
    unittest.main()
