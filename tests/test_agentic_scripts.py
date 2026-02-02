import os
import subprocess
import unittest
from pathlib import Path


class TestAgenticScripts(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.scripts_dir = self.repo_root / "scripts" / "agentic"

    def test_scripts_exist_and_executable(self):
        expected = [
            "run_swebench_multilingual.sh",
            "run_swebench_live_multilang.sh",
            "serve_vllm_model.sh",
            "stop_vllm_model.sh",
        ]
        for name in expected:
            path = self.scripts_dir / name
            self.assertTrue(path.is_file(), f"Missing script: {path}")
            self.assertTrue(os.access(path, os.X_OK), f"Script not executable: {path}")

    def test_scripts_pass_shellcheck_parse(self):
        for path in self.scripts_dir.glob("*.sh"):
            result = subprocess.run(
                ["bash", "-n", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"bash -n failed for {path}: {result.stderr}",
            )


if __name__ == "__main__":
    unittest.main()
