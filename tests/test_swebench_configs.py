"""Tests for mini-swe-agent model configuration files.

Validates that all 4 model configs (qwen3, deepseek, mixtral, gptoss) are
well-formed YAML with correct structure, required fields, and critical bug
fixes applied (submission command, format_error_template, timeout_template).
"""

import os
from pathlib import Path
import unittest

import yaml

CONFIGS_DIR = str(Path(__file__).resolve().parents[1] / "configs")
TEMPLATE_PATH = str(Path(CONFIGS_DIR) / "livesweagent.template.yaml")

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

# Submission commands expected for the two-step process.
SUBMISSION_STAGE_CMD = "git add -A"
SUBMISSION_FINAL_CMD = "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff --cached"
SUBMISSION_COMBINED_CMD = (
    "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached"
)


def _load_config(filename):
    """Load and parse a YAML config file."""
    path = os.path.join(CONFIGS_DIR, filename)
    with open(path) as f:
        return yaml.safe_load(f)

def _load_template_text():
    with open(TEMPLATE_PATH) as f:
        return f.read()

def _render_template(template_text, model_name):
    return template_text.replace("{{MODEL_NAME}}", model_name)


class TestConfigFilesExist(unittest.TestCase):
    """All 4 config files must exist."""

    def test_all_configs_exist(self):
        for name, info in EXPECTED_CONFIGS.items():
            path = os.path.join(CONFIGS_DIR, info["file"])
            self.assertTrue(
                os.path.exists(path),
                f"Config file missing for {name}: {path}",
            )
        self.assertTrue(
            os.path.exists(TEMPLATE_PATH),
            f"Template file missing: {TEMPLATE_PATH}",
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
    """All configs must include the two-step submission process.

    The submission is now split to avoid git warnings contaminating patches:
    1) git add -A
    2) echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff --cached
    """

    def test_instance_template_has_two_step_submission(self):
        for name, info in EXPECTED_CONFIGS.items():
            data = _load_config(info["file"])
            instance_tpl = data["agent"]["instance_template"]
            self.assertIn(
                SUBMISSION_STAGE_CMD, instance_tpl,
                f"{name} instance_template missing staging command",
            )
            self.assertIn(
                SUBMISSION_FINAL_CMD, instance_tpl,
                f"{name} instance_template missing final submission command",
            )
            self.assertNotIn(
                SUBMISSION_COMBINED_CMD, instance_tpl,
                f"{name} instance_template should not use combined submission command",
            )


class TestConfigConsistency(unittest.TestCase):
    """All configs must match the template (with model_name substituted)."""

    def setUp(self):
        self.template_text = _load_template_text()

    def test_configs_match_template(self):
        for name, info in EXPECTED_CONFIGS.items():
            rendered = _render_template(self.template_text, info["model_name"])
            actual = Path(CONFIGS_DIR, info["file"]).read_text()
            self.assertEqual(
                rendered, actual,
                f"{name} config differs from template output.",
            )


if __name__ == "__main__":
    unittest.main()
