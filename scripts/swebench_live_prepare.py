#!/usr/bin/env python3
"""Prepare SWE-bench-Live for MultiLang evaluation (submodule + evaluation patch)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def patch_evaluation(path: Path) -> bool:
    text = path.read_text()
    if "row = instances[idx]" in text and "todos.append(row)" in text:
        return False

    lines = text.splitlines()
    try:
        start = next(
            i for i, line in enumerate(lines) if "for idx in range(len(instances)):" in line
        )
        end = next(
            i for i, line in enumerate(lines[start + 1 :], start + 1)
            if "results = run_instances" in line
        )
    except StopIteration as exc:
        raise RuntimeError("Unable to locate evaluation loop for patching.") from exc

    indent = lines[start].split("for")[0]
    block = [
        f"{indent}for idx in range(len(instances)):",
        f"{indent}    row = instances[idx]",
        f"{indent}    if instance_ids is not None and row[\"instance_id\"] not in instance_ids:",
        f"{indent}        continue",
        f"{indent}    if patch_dir.strip() != \"gold\" and row[\"instance_id\"] in preds.keys():",
        f"{indent}        row[\"pred_patch\"] = preds[row[\"instance_id\"]][\"model_patch\"]",
        f"{indent}        todos.append(row)",
        f"{indent}    if patch_dir.strip() == \"gold\":",
        f"{indent}        row[\"pred_patch\"] = row[\"patch\"]",
        f"{indent}        todos.append(row)",
    ]

    new_lines = lines[:start] + block + lines[end:]
    path.write_text("\n".join(new_lines) + "\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare SWE-bench-Live repo for MultiLang evaluation."
    )
    parser.add_argument(
        "--repo",
        default="~/work/swebench/SWE-bench-Live",
        help="Path to the SWE-bench-Live repo.",
    )
    args = parser.parse_args()

    repo = Path(args.repo).expanduser()
    if not repo.exists():
        print(f"Repo not found: {repo}", file=sys.stderr)
        return 2

    run(["git", "-C", str(repo), "submodule", "update", "--init", "launch"])

    evaluation_path = repo / "evaluation" / "evaluation.py"
    if not evaluation_path.exists():
        print(f"Missing evaluation file: {evaluation_path}", file=sys.stderr)
        return 3

    patched = patch_evaluation(evaluation_path)
    if patched:
        print(f"Patched evaluation loop in {evaluation_path}")
    else:
        print(f"Evaluation loop already patched in {evaluation_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
