# SWE-bench Multilingual Evaluation Runbook (DGX Spark)

This runbook documents how to execute the multilingual SWE-bench evaluations defined in `ralph/plans/SPECIFICATION.md` using vLLM on DGX Spark. It is intentionally structured to mirror the execution plan and to capture reproducible results.

## Scope

- Suites:
  - SWE-bench Multilingual
  - SWE-bench-Live MultiLang
- Models (run in order):
  1. `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`
  2. `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
  3. `MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ`
  4. `openai/gpt-oss-120b`
- Serving image: `nvcr.io/nvidia/vllm:25.12.post1-py3`

## Prerequisites

- Docker installed and GPU access verified.
- Docker daemon running with enough disk for per-instance images (SWE-bench pulls from `swebench/*`; SWE-bench-Live pulls `starryzhang/sweb.eval.*`).
- DGX Spark is `aarch64`, but the SWE-bench evaluation images are `linux/amd64` only. Install binfmt/QEMU and force amd64 execution before running evaluations:
  ```
  docker run --privileged --rm tonistiigi/binfmt --install amd64
  export DOCKER_DEFAULT_PLATFORM=linux/amd64
  ```
  Verify with: `docker run --rm --platform=linux/amd64 alpine:3.19 uname -m` (should print `x86_64`).
- Docker Hub rate limits can break evaluations. Authenticate before running harnesses:
  ```
  docker login
  ```
  Optionally pre-pull images using `scripts/swebench_pull_images.py` (see below) to warm the cache.
- HuggingFace cache available at `~/Models/huggingface`.
- HuggingFace token file at `~/.cache/huggingface/token`.
- Adequate disk space for datasets and harness checkouts.

## Directory Layout

Suggested local working directory structure (outside this repo):

```
~/work/swebench/
  SWE-bench/
  SWE-bench-Live/
  runs/
    swebench-multilingual/
    swebench-live-multilang/
```

## Agentic Evaluation with mini-swe-agent (Recommended)

The recommended evaluation approach uses **mini-swe-agent**, an iterative agent framework that explores codebases, runs commands, and generates patches autonomously.

### Framework Setup

```bash
cd ~/work/swebench
git clone https://github.com/SWE-agent/mini-swe-agent.git
cd mini-swe-agent
source ~/work/swebench/.venv/bin/activate
pip install -e .
```

Clone **live-swe-agent** for optimized configuration files:
```bash
cd ~/work/swebench
git clone https://github.com/OpenAutoCoder/live-swe-agent.git
```

### Model Configurations

Each model has a dedicated config file at `~/work/swebench/configs/`:

| Config File | Model | vLLM Model ID |
|---|---|---|
| `qwen3-livesweagent.yaml` | Qwen3-Coder-30B-A3B-Instruct-FP8 | `hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` |
| `deepseek-livesweagent.yaml` | DeepSeek-Coder-V2-Lite-Instruct | `hosted_vllm/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` |
| `mixtral-livesweagent.yaml` | Mixtral-8x22B-Instruct-v0.1-AWQ | `hosted_vllm/MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ` |
| `gptoss-livesweagent.yaml` | gpt-oss-120b | `hosted_vllm/openai/gpt-oss-120b` |

All configs are based on `live-swe-agent/config/livesweagent.yaml` with these modifications:
- **Model endpoint**: Points to local vLLM at `http://localhost:8000/v1`
- **Cost tracking**: Set to `ignore_errors` (local inference has no cost)
- **Working directory**: Set to `/testbed` (Docker container path)
- **Submission command fix**: Includes `git add -A && git diff --cached` to capture patches
- **Timeout template**: Added (required by mini-swe-agent but missing from base config)
- **System info**: Hardcoded `Linux x86_64 (Docker container)` instead of Jinja2 variables

### Running Agentic Evaluations

**SWE-bench Multilingual:**
```bash
cd ~/work/swebench && source .venv/bin/activate
mini-extra swebench \
  --config configs/qwen3-livesweagent.yaml \
  --subset multilingual \
  --split test \
  --workers 1 \
  --output /path/to/output/
```

**SWE-bench-Live MultiLang (8 language splits):**
```bash
for split in c cpp go js rust java ts cs; do
  mini-extra swebench \
    --config configs/qwen3-livesweagent.yaml \
    --subset "SWE-bench-Live/MultiLang" \
    --split $split \
    --workers 1 \
    --output /path/to/output/$split/
done
```

**Important**: Do NOT pass `--model` on the command line. The model is configured in the YAML file. Passing `--model` on the CLI overrides the config and causes model name mismatch errors.

### Config Validation Tests

Run tests to verify all configs are well-formed:
```bash
python -m unittest tests.test_swebench_configs -v
```

---

## Direct Inference Harness Setup (Legacy)

> **Note**: The sections below document the original direct inference approach using SWE-bench harness scripts. The project has pivoted to agentic evaluation (see above). These instructions are retained for reference.

### Harness Setup

1. Clone the harness repositories:

```
cd ~/work/swebench

git clone https://github.com/SWE-bench/SWE-bench.git

git clone https://github.com/microsoft/SWE-bench-Live.git
```

2. Record harness commit hashes for reporting:

```
cd ~/work/swebench/SWE-bench

git rev-parse HEAD
```

3. Prepare SWE-bench-Live for MultiLang evaluation (submodule init + evaluation fix):

```
python scripts/swebench_live_prepare.py --repo ~/work/swebench/SWE-bench-Live
```

```
cd ~/work/swebench/SWE-bench-Live

git rev-parse HEAD
```

## Dataset Acquisition

Download datasets using each harness's recommended method. Record dataset version identifiers (tags/commit hashes) in the final report.

- SWE-bench Multilingual dataset: `SWE-bench/SWE-bench_Multilingual`
- SWE-bench-Live MultiLang dataset: `SWE-bench-Live/MultiLang`

## vLLM Serving

Use the exact serve commands from `ralph/plans/SPECIFICATION.md`. Start one model at a time, and only proceed to the next model after both suites complete.

### ⚠️ DGX Spark Unified Memory Constraints

**CRITICAL**: DGX Spark (GB10 with Grace CPU) uses unified memory where GPU and system RAM share the same 128GB pool. By default, vLLM allocates ALL available GPU memory for KV cache, consuming nearly all system RAM and causing OOM crashes.

**Required vLLM parameters** (discovered via investigation in Jan 2026):
- `--max-model-len 65536`: Limits context to 64K tokens
- `--gpu-memory-utilization 0.85`: Prevents consuming all system memory
- `--max-num-seqs 1`: Limits concurrent sequences for single-agent evaluation

Without these parameters, vLLM consumes ~104GB leaving only ~4GB for system operations, causing crashes during agent evaluation. With these parameters: model weights (~29GB) + KV cache (~70GB) + system (~11GB) = ~110GB stable usage.

See `ralph/plans/SPECIFICATION.md` Section 3.1 for memory breakdown and investigation details.

### Example (Qwen3)

```bash
docker run -d --name vllm-qwen3-coder --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --max-model-len 65536 \
  --gpu-memory-utilization 0.85 \
  --max-num-seqs 1
```

## Evaluation Runs

For each model, run both suites in order:

1. SWE-bench Multilingual (verified split)
2. SWE-bench-Live MultiLang (verified split)

### Generate Predictions via vLLM

Use `scripts/swebench_generate_predictions.py` to generate patch predictions from the vLLM OpenAI-compatible endpoint. The script sanitizes patches by default (strips code fences and trims whitespace) and writes both `model_patch` and `pred_patch` for compatibility with both harnesses. Activate the SWE-bench venv first:

```
source ~/work/swebench/.venv/bin/activate
```

SWE-bench Multilingual (JSONL output for `swebench.harness.run_evaluation`):

```
python scripts/swebench_generate_predictions.py \
  --suite swebench-multilingual \
  --model "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --output ~/work/swebench/runs/swebench-multilingual/qwen3-predictions.jsonl
```

SWE-bench-Live MultiLang (JSON mapping for `evaluation.evaluation`):

```
python scripts/swebench_generate_predictions.py \
  --suite swebench-live-multilang \
  --model "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --output ~/work/swebench/runs/swebench-live-multilang/qwen3-predictions.json
```

Use `--max-instances` for a short smoke test and `--dry-run` to validate output formatting without calling the API.
Use `--no-sanitize-diff` only if you need raw model output for debugging.

### Run Evaluations

Capture logs for each run in:

```
ralph/logs/swebench/<suite>/<model>/<run_id>/
```

Record any flags or deviations (Docker vs native, max model length, trust-remote-code, etc.).

#### SWE-bench Multilingual (SWE-bench harness)

Run the evaluation from the SWE-bench harness repo (installed editable). The harness requires a `run_id` and will
write `evaluation_results/` plus `logs/run_evaluation/` under the current working directory.

```
cd ~/work/swebench/SWE-bench

python -m swebench.harness.run_evaluation \
  --dataset_name SWE-bench/SWE-bench_Multilingual \
  --split test \
  --predictions_path ~/work/swebench/runs/swebench-multilingual/qwen3-predictions.jsonl \
  --max_workers 8 \
  --run_id qwen3-swebench-multilingual \
  --report_dir ~/work/swebench/runs/swebench-multilingual/reports
```

After each run, copy logs/results into the repo logs directory:

```
rsync -a --delete \
  ~/work/swebench/SWE-bench/logs/run_evaluation/qwen3-swebench-multilingual/ \
  ralph/logs/swebench/swebench-multilingual/qwen3/qwen3-swebench-multilingual/

rsync -a --delete \
  ~/work/swebench/SWE-bench/evaluation_results/ \
  ralph/logs/swebench/swebench-multilingual/qwen3/qwen3-swebench-multilingual/evaluation_results/
```

Adjust `--max_workers` for available CPU capacity.

#### SWE-bench-Live MultiLang (SWE-bench-Live harness)

Run the evaluation from the SWE-bench-Live repo. MultiLang uses per-language splits, so run each split and store
outputs separately. The harness writes results into the provided `--output_dir`.

```
cd ~/work/swebench/SWE-bench-Live

for split in c cpp go js rust java ts cs; do
  python -m evaluation.evaluation \
    --dataset SWE-bench-Live/MultiLang \
    --split "${split}" \
    --platform linux \
    --patch_dir ~/work/swebench/runs/swebench-live-multilang/qwen3-predictions.json \
    --output_dir ~/work/swebench/runs/swebench-live-multilang/results/qwen3/"${split}" \
    --workers 10 \
    --overwrite 0
done
```

Copy results into the repo logs directory:

```
rsync -a --delete \
  ~/work/swebench/runs/swebench-live-multilang/results/qwen3/ \
  ralph/logs/swebench/swebench-live-multilang/qwen3/
```

Use `--overwrite 1` when rerunning a split.

## Docker Image Pre-pull (Rate-Limit Mitigation)

To reduce Docker Hub 429 errors, pre-pull the per-instance images before running evaluations.
The helper script reads the dataset rows and pulls all referenced images.

SWE-bench Multilingual:

```
python scripts/swebench_pull_images.py --suite swebench-multilingual --require-auth
```

SWE-bench-Live MultiLang:

```
python scripts/swebench_pull_images.py --suite swebench-live-multilang --require-auth
```

Use `--dry-run` to list images without pulling, and `--output <path>` to save the image list.

## Reporting

Use the report template at `ralph/plans/SWE_BENCH_MULTILINGUAL_REPORT_TEMPLATE.md`.

Minimum metrics per model x suite:

- Total tasks in verified split
- Number solved / pass rate (or closest available metric)
- Known errors/failures affecting results

### Metrics Collection Helper

After completing evaluations, use `scripts/swebench_report_metrics.py` to extract metrics from
the SWE-bench harness report and SWE-bench-Live results directories:

```
python scripts/swebench_report_metrics.py \
  --model "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --swebench-report ~/work/swebench/SWE-bench/Qwen__Qwen3-Coder-30B-A3B-Instruct-FP8.qwen3-swebench-multilingual.json \
  --live-results-root ~/work/swebench/runs/swebench-live-multilang/results/qwen3 \
  --format markdown
```

Use `--output <path>` to save JSON or markdown into the run directory for later reporting.

## Notes and Deviations

If any suite cannot be run in Docker, document the exact reason and the native execution steps used.
