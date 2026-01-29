#!/usr/bin/env python3
"""Collect SWE-bench Multilingual and SWE-bench-Live MultiLang metrics."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_LIVE_SPLITS = ["c", "cpp", "go", "js", "rust", "java", "ts", "cs"]


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}.")
    return data


def safe_divide(numerator: int, denominator: int) -> float:
    return (numerator / denominator) if denominator else 0.0


def calculate_swebench_metrics(report_path: str) -> Dict[str, Any]:
    report = read_json(report_path)
    total = int(report.get("total_instances", 0))
    solved = int(report.get("resolved_instances", 0))
    errors = int(report.get("error_instances", 0))
    return {
        "total_tasks": total,
        "solved": solved,
        "pass_rate": safe_divide(solved, total),
        "errors": errors,
    }


def parse_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def calculate_live_metrics(results_root: str, splits: Iterable[str]) -> Dict[str, Any]:
    totals = {"total_tasks": 0, "solved": 0, "errors": 0}
    split_metrics: Dict[str, Any] = {}
    for split in splits:
        results_path = os.path.join(results_root, split, "results.json")
        data = read_json(results_path)
        success = int(data.get("success", 0))
        failure = int(data.get("failure", 0))
        error = int(data.get("error", 0))
        total = success + failure + error
        split_metrics[split] = {
            "total_tasks": total,
            "solved": success,
            "pass_rate": safe_divide(success, total),
            "errors": error,
        }
        totals["total_tasks"] += total
        totals["solved"] += success
        totals["errors"] += error
    return {
        **totals,
        "pass_rate": safe_divide(totals["solved"], totals["total_tasks"]),
        "splits": split_metrics,
    }


def render_markdown(metrics: Dict[str, Any]) -> str:
    lines = []
    if metrics.get("model"):
        lines.append(f"Model: {metrics['model']}")
    swebench = metrics.get("swebench_multilingual")
    if swebench:
        lines.append(
            "SWE-bench Multilingual: "
            f"total={swebench['total_tasks']}, solved={swebench['solved']}, "
            f"pass_rate={swebench['pass_rate']:.4f}, errors={swebench['errors']}"
        )
    live = metrics.get("swebench_live_multilang")
    if live:
        lines.append(
            "SWE-bench-Live MultiLang: "
            f"total={live['total_tasks']}, solved={live['solved']}, "
            f"pass_rate={live['pass_rate']:.4f}, errors={live['errors']}"
        )
        lines.append("Per-split:")
        for split, split_metrics in live["splits"].items():
            lines.append(
                f"- {split}: total={split_metrics['total_tasks']}, "
                f"solved={split_metrics['solved']}, "
                f"pass_rate={split_metrics['pass_rate']:.4f}, "
                f"errors={split_metrics['errors']}"
            )
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect metrics from SWE-bench Multilingual and SWE-bench-Live MultiLang results."
    )
    parser.add_argument("--model", help="Model name for reporting (optional).")
    parser.add_argument(
        "--swebench-report",
        help="Path to SWE-bench harness report JSON (model.run_id.json).",
    )
    parser.add_argument(
        "--live-results-root",
        help="Root directory containing per-split SWE-bench-Live results.json files.",
    )
    parser.add_argument(
        "--live-splits",
        default="",
        help="Comma-separated SWE-bench-Live MultiLang splits (default: all).",
    )
    parser.add_argument(
        "--output",
        help="Write metrics to this file (defaults to stdout).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format for metrics.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if not args.swebench_report and not args.live_results_root:
        raise SystemExit("Provide --swebench-report, --live-results-root, or both.")

    payload: Dict[str, Any] = {}
    if args.model:
        payload["model"] = args.model
    if args.swebench_report:
        payload["swebench_multilingual"] = calculate_swebench_metrics(args.swebench_report)
    if args.live_results_root:
        splits = parse_csv_list(args.live_splits) or DEFAULT_LIVE_SPLITS
        payload["swebench_live_multilang"] = calculate_live_metrics(args.live_results_root, splits)

    if args.format == "markdown":
        output = render_markdown(payload)
    else:
        output = json.dumps(payload, indent=2)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
            if not output.endswith("\n"):
                handle.write("\n")
    else:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
