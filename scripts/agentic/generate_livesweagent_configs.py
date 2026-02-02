#!/usr/bin/env python3
"""Generate model-specific live-swe-agent configs from a template."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = ROOT / "configs"
TEMPLATE_PATH = CONFIGS_DIR / "livesweagent.template.yaml"

MODEL_MAP = {
    "qwen3": "hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8",
    "deepseek": "hosted_vllm/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    "mixtral": "hosted_vllm/MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ",
    "gptoss": "hosted_vllm/openai/gpt-oss-120b",
}

OUTPUT_FILES = {
    "qwen3": CONFIGS_DIR / "qwen3-livesweagent.yaml",
    "deepseek": CONFIGS_DIR / "deepseek-livesweagent.yaml",
    "mixtral": CONFIGS_DIR / "mixtral-livesweagent.yaml",
    "gptoss": CONFIGS_DIR / "gptoss-livesweagent.yaml",
}


def main() -> int:
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: missing template: {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template = TEMPLATE_PATH.read_text()
    if "{{MODEL_NAME}}" not in template:
        print("ERROR: template missing {{MODEL_NAME}} placeholder", file=sys.stderr)
        return 1

    for key, model_name in MODEL_MAP.items():
        out_path = OUTPUT_FILES[key]
        rendered = template.replace("{{MODEL_NAME}}", model_name)
        out_path.write_text(rendered)
        print(f"wrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
