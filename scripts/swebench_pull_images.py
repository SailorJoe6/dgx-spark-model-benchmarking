#!/usr/bin/env python3
"""Pre-pull SWE-bench Docker images to reduce Docker Hub rate-limit errors."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

DEFAULT_IMAGE_FIELDS = (
    "docker_image",
    "image",
    "container_image",
    "docker",
)

DOCKERHUB_AUTH_KEYS = (
    "https://index.docker.io/v1/",
    "https://registry-1.docker.io/v1/",
    "docker.io",
    "registry-1.docker.io",
)


def load_dataset_swebench(split: str) -> Iterable[dict[str, Any]]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:  # pragma: no cover - import error path
        raise RuntimeError(
            "datasets is required. Activate /home/sailorjoe6/work/swebench/.venv first."
        ) from exc
    return load_dataset("SWE-bench/SWE-bench_Multilingual", split=split)


def load_dataset_live(splits: Sequence[str]) -> list[tuple[str, Iterable[dict[str, Any]]]]:
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


def extract_image(
    row: dict[str, Any],
    image_field: Optional[str],
    fallback_fields: Sequence[str] = DEFAULT_IMAGE_FIELDS,
) -> Optional[str]:
    if image_field:
        value = row.get(image_field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None
    for field in fallback_fields:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def collect_images(rows: Iterable[dict[str, Any]], image_field: Optional[str]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        image = extract_image(row, image_field)
        if image:
            counter[image] += 1
    return counter


def has_dockerhub_auth(config_path: Path) -> bool:
    auth_config = os.environ.get("DOCKER_AUTH_CONFIG")
    if auth_config:
        try:
            data = json.loads(auth_config)
        except json.JSONDecodeError:
            data = {}
    else:
        if not config_path.exists():
            return False
        data = json.loads(config_path.read_text())

    auths = data.get("auths", {}) if isinstance(data, dict) else {}
    for key in auths:
        if any(token in key for token in DOCKERHUB_AUTH_KEYS):
            return True
    return False


def docker_pull(image: str, platform: str, dry_run: bool) -> bool:
    if dry_run:
        return True
    result = subprocess.run(
        ["docker", "pull", "--platform", platform, image],
        check=False,
    )
    return result.returncode == 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pre-pull SWE-bench Docker images to reduce Docker Hub rate limits."
    )
    parser.add_argument(
        "--suite",
        choices=["swebench-multilingual", "swebench-live-multilang"],
        required=True,
        help="Which suite to collect images from.",
    )
    parser.add_argument("--split", default="test", help="Split for SWE-bench Multilingual.")
    parser.add_argument(
        "--splits",
        default="",
        help="Comma-separated splits for SWE-bench-Live MultiLang (default: all).",
    )
    parser.add_argument(
        "--image-field",
        default="",
        help="Explicit image field in the dataset rows (default: auto-detect).",
    )
    parser.add_argument(
        "--platform",
        default="linux/amd64",
        help="Docker platform to pull (default: linux/amd64).",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=0,
        help="Limit number of images to pull (0 = no limit).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to sleep between pulls.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print images only.")
    parser.add_argument(
        "--require-auth",
        action="store_true",
        help="Fail if Docker Hub auth is missing.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop if any docker pull fails.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional path to write image list (one per line).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    image_field = args.image_field.strip() or None
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    if args.require_auth:
        config_path = Path("~/.docker/config.json").expanduser()
        if not has_dockerhub_auth(config_path):
            print(
                "Docker Hub auth not detected. Run `docker login` or set DOCKER_AUTH_CONFIG.",
                file=sys.stderr,
            )
            return 2

    if args.suite == "swebench-multilingual":
        dataset = load_dataset_swebench(args.split)
        counter = collect_images(dataset, image_field)
    else:
        counter = Counter()
        for _, dataset in load_dataset_live(splits):
            counter.update(collect_images(dataset, image_field))

    images = [image for image, _ in counter.most_common()]
    if args.max_images:
        images = images[: args.max_images]

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(images) + ("\n" if images else ""))

    if not images:
        print("No docker images found in dataset rows.")
        return 1

    total = len(images)
    failures = []
    for idx, image in enumerate(images, start=1):
        print(f"[{idx}/{total}] {image}")
        ok = docker_pull(image, args.platform, args.dry_run)
        if not ok:
            failures.append(image)
            print(f"Failed to pull {image}", file=sys.stderr)
            if args.stop_on_error:
                break
        if args.sleep > 0:
            time.sleep(args.sleep)

    if failures:
        print(f"Failures: {len(failures)}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
