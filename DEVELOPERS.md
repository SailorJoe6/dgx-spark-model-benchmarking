# Developer Guide

This repo contains the evaluation configs, scripts, and docs for SWE-bench Multilingual and SWE-bench-Live MultiLang on DGX Spark. The `ralph/` folder is out of scope for this project.

## Layout

- Repo root: `configs/`, `scripts/`, `tests/`, `docs/`, `logs/`
- Workspace: `work/swebench/`
  - `.venv` virtualenv
  - `runs/` outputs (predictions, results, reports)
  - Submodules:
    - `work/swebench/mini-swe-agent`
    - `work/swebench/live-swe-agent`
    - `work/swebench/SWE-bench`
    - `work/swebench/SWE-bench-Live`

`work/swebench/configs` and `work/swebench/scripts` are symlinks back to the repo root for convenience.

## Setup

1. Initialize submodules:
   ```bash
   git submodule update --init --recursive
   ```
2. Create a virtualenv in the workspace:
   ```bash
   python3 -m venv work/swebench/.venv
   source work/swebench/.venv/bin/activate
   pip install -U pip
   ```
3. Install mini-swe-agent from the submodule:
   ```bash
   pip install -e work/swebench/mini-swe-agent
   ```
4. Ensure HuggingFace auth and cache:
   - Token: `~/.cache/huggingface/token`
   - Cache: `~/Models/huggingface`

## Running Evaluations

Follow the runbook in `docs/swe-bench-multilingual-evaluation.md`. The canonical workspace path is:

```
/home/sailorjoe6/Code/swebench-eval/work/swebench
```

Configs live in `configs/` (also available at `work/swebench/configs`). vLLM should be run via Docker as shown in the runbook.

## Scripts

All scripts are in `scripts/`:

- `scripts/monitor_memory.sh` - memory monitoring during runs
- `scripts/swebench_generate_predictions.py` - generate prediction files via vLLM endpoint
- `scripts/swebench_pull_images.py` - pre-pull SWE-bench Docker images
- `scripts/swebench_live_prepare.py` - patch SWE-bench-Live evaluation loop
- `scripts/swebench_report_metrics.py` - summarize metrics

## Tests

Most tests are standard `unittest`:

```bash
python -m unittest discover -s tests -v
```

Notes:
- `tests/test_litellm_streaming.py` requires vLLM running at `http://localhost:8000/v1` and the `mini-swe-agent` submodule present.
- `tests/test_swebench_configs.py` validates the config files under `configs/`.

## Issue Tracking

This project uses `bd` (beads) for issue tracking. See `AGENTS.md` for the workflow.
