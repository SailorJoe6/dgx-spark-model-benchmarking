#!/usr/bin/env python3
"""Generate SWE-bench patch predictions from a vLLM OpenAI-compatible endpoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

DEFAULT_API_BASE = "http://localhost:8000/v1"
DEFAULT_SYSTEM_PROMPT = (
    "You are an expert software engineer. Produce a unified diff patch that fixes the issue. "
    "Return only the diff, with no extra commentary."
)


def build_user_prompt(instance: Dict[str, Any]) -> str:
    parts = [
        "You will be given a repository issue to fix.",
        "Return a unified diff patch that applies cleanly.",
        "",
        f"Repository: {instance.get('repo', '').strip()}",
        f"Instance ID: {instance.get('instance_id', '').strip()}",
        "",
        "Problem Statement:",
        instance.get("problem_statement", "").strip(),
    ]
    hints = instance.get("hints_text", "") or instance.get("all_hints_text", "")
    hints = (hints or "").strip()
    if hints:
        parts.extend(["", "Hints:", hints])
    return "\n".join(parts).strip() + "\n"


def parse_csv_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def load_dataset_swebench(split: str) -> Iterable[Dict[str, Any]]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:  # pragma: no cover - import error path
        raise RuntimeError(
            "datasets is required. Activate /home/sailorjoe6/work/swebench/.venv first."
        ) from exc
    return load_dataset("SWE-bench/SWE-bench_Multilingual", split=split)


def load_dataset_live(splits: Sequence[str]) -> List[Tuple[str, Iterable[Dict[str, Any]]]]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:  # pragma: no cover - import error path
        raise RuntimeError(
            "datasets is required. Activate /home/sailorjoe6/work/swebench/.venv first."
        ) from exc
    dataset = load_dataset("SWE-bench-Live/MultiLang")
    if not splits:
        splits = list(dataset.keys())
    return [(split, dataset[split]) for split in splits]


def openai_chat_completion(
    api_base: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
    timeout: int,
    api_key: Optional[str],
) -> str:
    url = f"{api_base.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
    result = json.loads(body)
    return result["choices"][0]["message"]["content"]


def sanitize_patch(patch: str) -> str:
    if not patch:
        return ""
    stripped = patch.strip()
    if not stripped:
        return ""
    lines = stripped.splitlines()
    if any(line.strip().startswith("```") for line in lines):
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
        else:
            start = None
            end = None
            for idx, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start is None:
                        start = idx
                    else:
                        end = idx
                        break
            if start is not None and end is not None and end > start:
                lines = lines[start + 1 : end]
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def read_existing_swebench_predictions(path: str) -> Set[str]:
    if not os.path.exists(path):
        return set()
    instance_ids: Set[str] = set()
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            instance_id = data.get("instance_id")
            if instance_id:
                instance_ids.add(instance_id)
    return instance_ids


def append_jsonl(path: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_existing_live_predictions(path: str) -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object mapping instance_id to patch entries.")
    return data


def write_live_predictions(path: str, payload: Dict[str, Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def generate_patch(
    api_base: str,
    model: str,
    instance: Dict[str, Any],
    temperature: float,
    max_tokens: int,
    timeout: int,
    api_key: Optional[str],
    dry_run: bool,
) -> str:
    messages = [
        {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(instance)},
    ]
    if dry_run:
        return ""
    return openai_chat_completion(
        api_base=api_base,
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        api_key=api_key,
    )


def run_swebench(args: argparse.Namespace) -> None:
    dataset = load_dataset_swebench(args.split)
    seen = read_existing_swebench_predictions(args.output) if args.resume else set()
    processed = 0
    for instance in dataset:
        instance_id = instance["instance_id"]
        if instance_id in seen:
            continue
        patch = generate_patch(
            api_base=args.api_base,
            model=args.model,
            instance=instance,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            api_key=args.api_key,
            dry_run=args.dry_run,
        )
        if args.sanitize_diff:
            patch = sanitize_patch(patch)
        append_jsonl(
            args.output,
            {
                "instance_id": instance_id,
                "model_name_or_path": args.model,
                "model_patch": patch,
                "pred_patch": patch,
            },
        )
        processed += 1
        if args.max_instances and processed >= args.max_instances:
            break
        if args.sleep > 0:
            time.sleep(args.sleep)


def run_live(args: argparse.Namespace) -> None:
    splits = parse_csv_list(args.splits)
    dataset_splits = load_dataset_live(splits)
    predictions = read_existing_live_predictions(args.output) if args.resume else {}
    processed = 0
    for split, dataset in dataset_splits:
        for instance in dataset:
            instance_id = instance["instance_id"]
            if instance_id in predictions:
                continue
            patch = generate_patch(
                api_base=args.api_base,
                model=args.model,
                instance=instance,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
                api_key=args.api_key,
                dry_run=args.dry_run,
            )
            if args.sanitize_diff:
                patch = sanitize_patch(patch)
            predictions[instance_id] = {"model_patch": patch, "pred_patch": patch}
            write_live_predictions(args.output, predictions)
            processed += 1
            if args.max_instances and processed >= args.max_instances:
                return
            if args.sleep > 0:
                time.sleep(args.sleep)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SWE-bench prediction patches via vLLM OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--suite",
        choices=["swebench-multilingual", "swebench-live-multilang"],
        required=True,
        help="Which suite to generate predictions for.",
    )
    parser.add_argument("--model", required=True, help="Model name as served by vLLM.")
    parser.add_argument("--output", required=True, help="Output path for predictions.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="OpenAI API base URL.")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY"), help="Optional API key.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Max tokens to generate.")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout (seconds).")
    parser.add_argument("--max-instances", type=int, default=0, help="Limit number of instances.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between requests.")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls, write empty patches.")
    parser.add_argument(
        "--no-sanitize-diff",
        dest="sanitize_diff",
        action="store_false",
        help="Disable patch sanitization (strip code fences/whitespace).",
    )
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Do not resume.")
    parser.set_defaults(resume=True, sanitize_diff=True)
    parser.add_argument("--split", default="test", help="Dataset split for SWE-bench Multilingual.")
    parser.add_argument(
        "--splits",
        default="",
        help="Comma-separated splits for SWE-bench-Live MultiLang (default: all).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.suite == "swebench-multilingual":
        run_swebench(args)
    else:
        run_live(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
