"""Tests for mini-swe-agent model configuration files.

Validates that all 4 model configs (qwen3, deepseek, mixtral, gptoss) are
well-formed YAML with correct structure, required fields, and critical bug
fixes applied (submission command, format_error_template, timeout_template).
"""

import os
import unittest

import yaml

CONFIGS_DIR = os.path.join(
    os.path.expanduser("~"), "work", "swebench", "configs"
)

EXPECTED_CONFIGS = {
    "qwen3": {
        "file": "qwen3-livesweagent.yaml",
        "model_name": "hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8",
    },
    "deepseek": {
        "file": "deepseek-livesweagent.yaml",
        "model_name": "hosted_vllm/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    },
    "mixtral": {
        "file": "mixtral-livesweagent.yaml",
        "model_name": "hosted_vllm/MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ",
    },
    "gptoss": {
        "file": "gptoss-livesweagent.yaml",
        "model_name": "hosted_vllm/openai/gpt-oss-120b",
    },
}

# The submission command that must appear in configs (bug fix for empty patches)
SUBMISSION_COMMAND = "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached"


def _load_config(filename):
    """Load and parse a YAML config file."""
    path = os.path.join(CONFIGS_DIR, filename)
    with open(path) as f:
        return yaml.safe_load(f)


class TestConfigFilesExist(unittest.TestCase):
    """All 4 config files must exist."""

    def test_all_configs_exist(self):
        for name, info in EXPECTED_CONFIGS.items():
            path = os.path.join(CONFIGS_DIR, info["file"])
            self.assertTrue(
                os.path.exists(path),
                f"Config file missing for {name}: {path}",
            )


class TestConfigYAMLValidity(unittest.TestCase):
    """All configs must be valid YAML."""

    def test_all_configs_parse(self):
        for name, info in EXPECTED_CONFIGS.items():
            try:
                data = _load_config(info["file"])
                self.assertIsInstance(data, dict, f"{name} config is not a dict")
            except yaml.YAMLError as e:
                self.fail(f"{name} config has invalid YAML: {e}")


class TestConfigStructure(unittest.TestCase):
    """Each config must have the required top-level sections and fields."""

    def setUp(self):
        self.configs = {
            name: _load_config(info["file"])
            for name, info in EXPECTED_CONFIGS.items()
        }

    def test_top_level_sections(self):
        for name, data in self.configs.items():
            for section in ("agent", "environment", "model"):
                self.assertIn(
                    section, data, f"{name} missing top-level '{section}'"
                )

    def test_agent_templates(self):
        required_templates = [
            "system_template",
            "instance_template",
            "action_observation_template",
            "format_error_template",
            "timeout_template",
        ]
        for name, data in self.configs.items():
            agent = data["agent"]
            for tpl in required_templates:
                self.assertIn(
                    tpl, agent, f"{name} missing agent.{tpl}"
                )
                self.assertIsInstance(
                    agent[tpl], str, f"{name} agent.{tpl} is not a string"
                )

    def test_agent_limits(self):
        for name, data in self.configs.items():
            agent = data["agent"]
            self.assertIn("step_limit", agent, f"{name} missing step_limit")
            self.assertIn("cost_limit", agent, f"{name} missing cost_limit")
            self.assertIn("mode", agent, f"{name} missing mode")

    def test_environment_fields(self):
        for name, data in self.configs.items():
            env = data["environment"]
            self.assertEqual(
                env.get("cwd"), "/testbed",
                f"{name} environment.cwd must be '/testbed'",
            )
            self.assertEqual(
                env.get("environment_class"), "docker",
                f"{name} environment_class must be 'docker'",
            )
            self.assertIn("timeout", env, f"{name} missing environment.timeout")
            self.assertIn("env", env, f"{name} missing environment.env")

    def test_model_fields(self):
        for name, data in self.configs.items():
            model = data["model"]
            self.assertIn("model_name", model, f"{name} missing model.model_name")
            self.assertEqual(
                model.get("cost_tracking"), "ignore_errors",
                f"{name} model.cost_tracking must be 'ignore_errors'",
            )
            self.assertIn(
                "model_kwargs", model, f"{name} missing model.model_kwargs"
            )
            kwargs = model["model_kwargs"]
            self.assertEqual(
                kwargs.get("api_base"), "http://localhost:8000/v1",
                f"{name} api_base must point to local vLLM",
            )
            self.assertTrue(
                kwargs.get("drop_params"),
                f"{name} model_kwargs.drop_params must be true",
            )


class TestConfigModelNames(unittest.TestCase):
    """Each config must have the correct model_name for its model."""

    def test_model_names_match(self):
        for name, info in EXPECTED_CONFIGS.items():
            data = _load_config(info["file"])
            actual = data["model"]["model_name"]
            expected = info["model_name"]
            self.assertEqual(
                actual, expected,
                f"{name} model_name mismatch: got '{actual}', expected '{expected}'",
            )


class TestSubmissionCommandFix(unittest.TestCase):
    """All configs must include the submission command bug fix.

    The original livesweagent.yaml instructed agents to run just
    'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' which produces empty patches.
    The fix appends '&& git add -A && git diff --cached' to capture the patch.
    """

    def test_instance_template_has_submission_fix(self):
        for name, info in EXPECTED_CONFIGS.items():
            data = _load_config(info["file"])
            instance_tpl = data["agent"]["instance_template"]
            self.assertIn(
                SUBMISSION_COMMAND, instance_tpl,
                f"{name} instance_template missing submission command fix",
            )

    def test_format_error_template_has_submission_fix(self):
        for name, info in EXPECTED_CONFIGS.items():
            data = _load_config(info["file"])
            fmt_err = data["agent"]["format_error_template"]
            self.assertIn(
                SUBMISSION_COMMAND, fmt_err,
                f"{name} format_error_template missing submission command fix",
            )


class TestConfigConsistency(unittest.TestCase):
    """All configs must be structurally identical except for model_name."""

    def setUp(self):
        self.configs = {
            name: _load_config(info["file"])
            for name, info in EXPECTED_CONFIGS.items()
        }

    def _strip_model_name(self, data):
        """Return config with model_name and comment line neutralized."""
        import copy
        d = copy.deepcopy(data)
        d["model"]["model_name"] = "PLACEHOLDER"
        return d

    def test_all_configs_identical_except_model_name(self):
        stripped = {
            name: self._strip_model_name(data)
            for name, data in self.configs.items()
        }
        names = list(stripped.keys())
        reference_name = names[0]
        reference = stripped[reference_name]
        for name in names[1:]:
            self.assertEqual(
                reference, stripped[name],
                f"{name} config differs from {reference_name} "
                f"(beyond model_name). Configs must be structurally identical.",
            )


if __name__ == "__main__":
    unittest.main()
