#!/usr/bin/env python3
"""Emit standard blocked-status report for SWE-bench runs."""
from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "logs"
WORK = ROOT / "work" / "swebench"
LOGS_ALT = WORK / "logs"

MODELS = ["qwen3", "deepseek", "mixtral", "gptoss"]
LIVE_SPLITS = {
    "c": 31,
    "cpp": 17,
    "go": 68,
    "js": 75,
    "rust": 45,
    "java": 62,
    "ts": 87,
    "cs": 28,
}


def _ps_text() -> str:
    return subprocess.check_output("ps aux", shell=True, text=True)


def _running_generation(ps_text: str, model: str) -> bool:
    return (
        f"mini-extra swebench --config /home/sailorjoe6/work/swebench/configs/{model}-livesweagent.yaml --subset multilingual"
        in ps_text
    )


def _gen_process_line(ps_text: str) -> str | None:
    for line in ps_text.splitlines():
        if "mini-extra swebench" in line and "--subset multilingual" in line:
            return line.strip()
    return None


def _eval_process_line(ps_text: str) -> str | None:
    for line in ps_text.splitlines():
        if "swebench.harness.run_evaluation" in line:
            return line.strip()
    return None


def _load_json(path: Path):
    return json.loads(path.read_text())


def _select_preds_path(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _count_preds(paths: list[Path]) -> int:
    selected = _select_preds_path(paths)
    if selected is None:
        return 0
    return len(_load_json(selected))


def _preds_paths(suite: str, model: str, split: str | None = None) -> list[Path]:
    if suite == "multilingual":
        return [
            LOGS / "swebench-multilingual" / model / "preds.json",
            LOGS_ALT / "swebench-multilingual" / model / "preds.json",
        ]
    if split is None:
        raise ValueError("split is required for live-multilang suite")
    return [
        LOGS / "swebench-live-multilang" / model / split / "preds.json",
        LOGS_ALT / "swebench-live-multilang" / model / split / "preds.json",
    ]


def _suite_status():
    ps_text = _ps_text()
    multilingual = {}
    for model in MODELS:
        count = _count_preds(_preds_paths("multilingual", model))
        status = "done" if count >= 300 else ("running" if _running_generation(ps_text, model) else "waiting")
        multilingual[model] = (status, count, 300)

    live = {}
    for model in MODELS:
        split_counts = {}
        all_done = True
        for split, total in LIVE_SPLITS.items():
            count = _count_preds(_preds_paths("live-multilang", model, split))
            split_counts[split] = (count, total)
            if count < total:
                all_done = False
        status = "done" if all_done and split_counts else "waiting"
        live[model] = (status, split_counts)

    return multilingual, live, ps_text


def _latest_model_dir(run_root: Path) -> Path | None:
    if not run_root.exists():
        return None
    model_dirs = [p for p in run_root.iterdir() if p.is_dir()]
    if not model_dirs:
        return None
    model_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return model_dirs[0]


def _eval_stats():
    run_id = "qwen3-swebench-multilingual"
    run_root = WORK / "SWE-bench" / "logs" / "run_evaluation" / run_id
    model_dir = _latest_model_dir(run_root)
    if model_dir is None:
        return 0, 0, 0, 0, 0.0, None

    instance_dirs = [p for p in model_dir.iterdir() if p.is_dir()]
    total = len(instance_dirs)
    report_files = [p / "report.json" for p in instance_dirs if (p / "report.json").exists()]

    resolved = 0
    for rf in report_files:
        outer = _load_json(rf)
        inst = next(iter(outer))
        inner = outer[inst]
        if inner.get("resolved") is True:
            resolved += 1

    error_count = 0
    for inst_dir in instance_dirs:
        if (inst_dir / "report.json").exists():
            continue
        log_path = inst_dir / "run_instance.log"
        if not log_path.exists():
            continue
        text = log_path.read_text(errors="ignore")
        if "EvaluationError" in text or "Patch Apply Failed" in text or "ERROR - Error in evaluating model" in text:
            error_count += 1

    count = len(report_files)
    percent = (resolved / count * 100.0) if count else 0.0
    return total, count, error_count, resolved, percent, model_dir


def _load_preds(paths: list[Path]) -> tuple[dict, Path | None]:
    preds_path = _select_preds_path(paths)
    if preds_path is None:
        return {}, None
    return _load_json(preds_path), preds_path


def _patch_text(entry: dict) -> str | None:
    for key in ("model_patch", "patch"):
        value = entry.get(key)
        if value is not None:
            return value
    return None


def _dataset_status(preds: dict, model_dir: Path | None) -> Counter:
    counts: Counter = Counter()
    if not preds or model_dir is None:
        return counts

    for inst_id, entry in preds.items():
        patch = _patch_text(entry)
        if not patch or not str(patch).strip():
            counts["patch_empty"] += 1
            continue

        inst_dir = model_dir / inst_id
        report_path = inst_dir / "report.json"
        if report_path.exists():
            report = _load_json(report_path)
            inner = report.get(inst_id, {})
            if inner.get("resolved") is True:
                counts["resolved"] += 1
            elif inner.get("patch_successfully_applied") is True:
                counts["applied_tests_failed"] += 1
            elif inner.get("patch_successfully_applied") is False:
                counts["patch_apply_failed"] += 1
            else:
                counts["evaluated_unknown"] += 1
            continue

        log_path = inst_dir / "run_instance.log"
        if not log_path.exists():
            counts["not_evaluated"] += 1
            continue

        text = log_path.read_text(errors="ignore")
        if (
            "Patch Apply Failed" in text
            or "Only garbage was found in the patch input" in text
            or "patch unexpectedly ends in middle of line" in text
        ):
            counts["patch_apply_failed"] += 1
        elif "container" in text and "is not running" in text:
            counts["container_error"] += 1
        elif "Error in evaluating model" in text or "EvaluationError" in text:
            counts["eval_error"] += 1
        else:
            counts["eval_error"] += 1

    return counts


def _system_stats():
    free = subprocess.check_output("free -h", shell=True, text=True).strip().splitlines()
    uptime = subprocess.check_output("uptime", shell=True, text=True).strip()
    mpstat = subprocess.check_output("mpstat -P ALL 1 1", shell=True, text=True)
    gpu = subprocess.check_output(
        "nvidia-smi --query-gpu=name,utilization.gpu,utilization.memory,memory.total,memory.used --format=csv,noheader",
        shell=True,
        text=True,
    ).strip()
    return free, uptime, mpstat, gpu


def main() -> int:
    multilingual, live, ps_text = _suite_status()

    print("Summary (status by suite/model)")
    print("swebench-multilingual:")
    for model in MODELS:
        status, count, total = multilingual[model]
        print(f"- {model}: {status} (test: {count}/{total})")

    print("\nswebench-live-multilang:")
    for model in MODELS:
        status, splits = live[model]
        parts = ", ".join(f"{k}: {v[0]}/{v[1]}" for k, v in splits.items())
        print(f"- {model}: {status} ({parts})")

    # Generation
    preds_candidates = _preds_paths("multilingual", "qwen3")
    preds_path = _select_preds_path(preds_candidates)
    preds_count = _count_preds(preds_candidates)
    preds_pct = (preds_count / 300 * 100.0) if preds_count else 0.0
    gen_line = _gen_process_line(ps_text)
    print("\nGeneration (Qwen3 multilingual)")
    print(f"- preds.json entries: {preds_count} / 300 ({preds_pct:.2f}%)")
    if preds_path:
        print(f"- preds path: {preds_path}")
    else:
        print("- preds path: missing (checked repo logs + work logs)")
    if gen_line:
        print(f"- process running: {gen_line}")
    else:
        print("- process running: not running")

    # Evaluation
    total, reports, errors, resolved, resolved_pct, model_dir = _eval_stats()
    eval_line = _eval_process_line(ps_text)
    print("\nEvaluation")
    print(f"- reports written: {reports} / {total}")
    print(f"- errors logged: {errors} / {total}")
    print(f"- resolved: {resolved} / {reports} \u2192 {resolved_pct:.2f}%")
    if model_dir:
        print(f"- eval dir: {model_dir}")
    if eval_line:
        print(f"- process running: {eval_line}")
    else:
        print("- process running: not running")

    preds, _ = _load_preds(preds_candidates)
    dataset_counts = _dataset_status(preds, model_dir)
    if preds:
        print("\nDataset status (Qwen3 multilingual)")
        total_ds = len(preds)
        print(f"- total instances: {total_ds}")
        resolved_total = dataset_counts.get("resolved", 0)
        applied_failed = dataset_counts.get("applied_tests_failed", 0)
        apply_failed = dataset_counts.get("patch_apply_failed", 0)
        eval_errors = dataset_counts.get("eval_error", 0)
        container_errors = dataset_counts.get("container_error", 0)
        empty_patches = dataset_counts.get("patch_empty", 0)
        no_log = dataset_counts.get("not_evaluated", 0)
        evaluated_total = resolved_total + applied_failed + apply_failed + eval_errors + container_errors
        resolved_pct_eval = (resolved_total / evaluated_total * 100.0) if evaluated_total else 0.0
        resolved_pct_total = (resolved_total / total_ds * 100.0) if total_ds else 0.0
        not_through_eval = total_ds - evaluated_total
        print(f"- evaluated (tests attempted): {evaluated_total}")
        print(f"- resolved: {resolved_total} / {evaluated_total} \u2192 {resolved_pct_eval:.2f}%")
        print(f"- resolved of total: {resolved_total} / {total_ds} \u2192 {resolved_pct_total:.2f}%")
        print(f"- applied but tests failed: {applied_failed}")
        print(f"- patch apply failed (garbage/reversed): {apply_failed}")
        print(f"- patch empty: {empty_patches}")
        print(f"- eval errors (other): {eval_errors}")
        print(f"- container errors: {container_errors}")
        print(f"- not evaluated (no log): {no_log}")
        print(f"- not through test evaluation: {not_through_eval}")

    # System stats
    free, uptime, mpstat, gpu = _system_stats()
    print("\nSystem stats")
    for line in free:
        if line.startswith("Mem:"):
            parts = line.split()
            used = parts[2]
            total = parts[1]
            avail = parts[-1]
            print(f"- RAM: {used} / {total}, {avail} available")
        if line.startswith("Swap:"):
            parts = line.split()
            used = parts[2]
            total = parts[1]
            print(f"- Swap: {used} / {total}")
    # CPU summary from mpstat (Average all)
    for line in mpstat.splitlines():
        if line.startswith("Average:") and "all" in line:
            parts = line.split()
            # columns: CPU %usr %nice %sys %iowait %irq %soft %steal %guest %gnice %idle
            usr = parts[3]
            sys = parts[5]
            idle = parts[-1]
            print(f"- CPU: {usr}% user, {sys}% sys, {idle}% idle (load avg {uptime.split('load average:')[-1].strip()})")
            break
    # GPU
    if gpu:
        name, util, mem_util, *_ = [p.strip() for p in gpu.split(",")]
        print(f"- GPU: {util} util, {mem_util} mem util")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
