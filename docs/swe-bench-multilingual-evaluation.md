# SWE-bench Multilingual Evaluation Runbook (DGX Spark)

This runbook documents how to execute the multilingual SWE-bench evaluations using vLLM on DGX Spark. It is intentionally structured to capture reproducible results.

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
  **Note:** binfmt registrations are not persistent across reboots. Re-run the binfmt install after any reboot.
- Docker Hub rate limits can break evaluations. Authenticate before running harnesses:
  ```
  docker login
  ```
  Optionally pre-pull images using `scripts/swebench_pull_images.py` (see below) to warm the cache.
- HuggingFace cache available at `~/Models/huggingface`.
- HuggingFace token file at `~/.cache/huggingface/token`.
- Adequate disk space for datasets and harness checkouts.

## Blocked Workflow (Mandatory for Long Runs)

Once any long-running evaluation starts, the project is considered **BLOCKED** until completion.

Checklist:
1. Update the active beads issue to **blocked** and note the run start timestamp.
2. Update `docs/CURRENT_STATUS.md` with the run details and start time.
3. Unblock only after the run completes or is explicitly stopped.

## Memory Monitoring (Mandatory)

Start the memory monitor **before** any long-running agentic run:

```bash
cd /home/sailorjoe6/Code/swebench-eval/work/swebench && ./scripts/monitor_memory.sh &
```

## Directory Layout

Suggested local working directory structure (outside this repo):

```
/home/sailorjoe6/Code/swebench-eval/work/swebench/
  SWE-bench/
  SWE-bench-Live/
  runs/
    swebench-multilingual/
    swebench-live-multilang/
```

## Agentic Evaluation with mini-swe-agent (Recommended)

The recommended evaluation approach uses **mini-swe-agent**, an iterative agent framework that explores codebases, runs commands, and generates patches autonomously.

### Framework Setup

External dependencies are vendored as submodules under `work/swebench/`.

```bash
cd /home/sailorjoe6/Code/swebench-eval
git submodule update --init --recursive
source /home/sailorjoe6/Code/swebench-eval/work/swebench/.venv/bin/activate
pip install -e work/swebench/mini-swe-agent
```

Record submodule commit hash for reporting:
```bash
cd /home/sailorjoe6/Code/swebench-eval/work/swebench/mini-swe-agent && git rev-parse HEAD
```

### Model Configurations

Each model has a dedicated config file at `/home/sailorjoe6/Code/swebench-eval/work/swebench/configs/`:

| Config File | Model | vLLM Model ID |
|---|---|---|
| `qwen3-livesweagent.yaml` | Qwen3-Coder-30B-A3B-Instruct-FP8 | `hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8` |
| `deepseek-livesweagent.yaml` | DeepSeek-Coder-V2-Lite-Instruct | `hosted_vllm/deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` |
| `mixtral-livesweagent.yaml` | Mixtral-8x22B-Instruct-v0.1-AWQ | `hosted_vllm/MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ` |
| `gptoss-livesweagent.yaml` | gpt-oss-120b | `hosted_vllm/openai/gpt-oss-120b` |

All configs are maintained locally (originally inspired by upstream live-swe-agent settings) with these modifications:
- **Model endpoint**: Points to local vLLM at `http://localhost:8000/v1`
- **Cost tracking**: Set to `ignore_errors` (local inference has no cost)
- **Working directory**: Set to `/testbed` (Docker container path)
- **Docker platform**: `run_args` includes `--platform=linux/amd64` to run SWE-bench images on aarch64 hosts
- **Output cap**: `model_kwargs.max_completion_tokens: 65536` (per Qwen3 guidance)
- **XML stop sequences**: Disabled (stop list commented out) due to Qwen3 tool-call malformed JSON bug; see `docs/CURRENT_STATUS.md` for context
- **Submission command fix**: Use the default mini-swe-agent flow: create `patch.txt` via `git diff -- path/to/file1 path/to/file2 > patch.txt`, verify it, then submit with `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt`
- **Timeout template**: Added (required by mini-swe-agent but missing from base config)
- **System info**: Hardcoded `Linux x86_64 (Docker container)` instead of Jinja2 variables
- **Command timeout**: `environment.timeout: 1800` (30m) safety timeout for individual commands (no global evaluation timeout)

### Running Agentic Evaluations

**SWE-bench Multilingual:**
```bash
cd /home/sailorjoe6/Code/swebench-eval/work/swebench && source .venv/bin/activate
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

### Wrapper Scripts (Agentic)

For reproducible runs, use the helper scripts under `scripts/agentic/`:

**Run SWE-bench Multilingual:**
```bash
scripts/agentic/run_swebench_multilingual.sh \
  qwen3 \
  /home/sailorjoe6/Code/swebench-eval/work/swebench/configs/qwen3-livesweagent.yaml \
  /home/sailorjoe6/Code/swebench-eval/logs/swebench-multilingual/qwen3/
```

**Run SWE-bench-Live MultiLang (all splits):**
```bash
scripts/agentic/run_swebench_live_multilang.sh \
  qwen3 \
  /home/sailorjoe6/Code/swebench-eval/work/swebench/configs/qwen3-livesweagent.yaml \
  /home/sailorjoe6/Code/swebench-eval/logs/swebench-live-multilang/qwen3/
```

Script environment overrides:
- `WORKDIR` (default: `<repo>/work/swebench`)
- `WORKERS` (default: 1)
- `CONTINUE_ON_ERROR` (default: 1, for live-multilang script)

**Start/stop vLLM containers:**
```bash
# Start (model key: qwen3|deepseek|mixtral|gptoss)
scripts/agentic/serve_vllm_model.sh qwen3

# Stop
scripts/agentic/stop_vllm_model.sh qwen3
```

vLLM script environment overrides:
`VLLM_IMAGE`, `VLLM_PORT`, `VLLM_MAX_MODEL_LEN`, `VLLM_GPU_MEMORY_UTIL`,
`VLLM_MAX_NUM_SEQS`, `VLLM_KV_CACHE_DTYPE`, `VLLM_EXTRA_ARGS`,
`VLLM_HEALTH_URL`, `VLLM_HEALTH_TIMEOUT`.

### Config Validation Tests

Run tests to verify all configs are well-formed:
```bash
python -m unittest tests.test_swebench_configs -v
```

---

## Direct Inference Harness Setup (Legacy)

> **Note**: The sections below document the original direct inference approach using SWE-bench harness scripts. The project has pivoted to agentic evaluation (see above). These instructions are retained for reference only and should not be used for the current agentic runs.

**Legacy script status (2026-02-02 audit):**
1. `scripts/swebench_generate_predictions.py`: deprecated (direct inference only).
2. `scripts/swebench_report_metrics.py`: keep (still useful for report aggregation).
3. `scripts/swebench_pull_images.py`: keep (rate-limit mitigation).
4. `scripts/swebench_live_prepare.py`: keep (patch SWE-bench-Live harness if needed).

### Harness Setup

1. Ensure harness submodules are initialized:

```
cd /home/sailorjoe6/Code/swebench-eval
git submodule update --init --recursive
```

2. Record harness commit hashes for reporting:

```
cd /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench

git rev-parse HEAD
```

3. Prepare SWE-bench-Live for MultiLang evaluation (submodule init + evaluation fix):

```
python scripts/swebench_live_prepare.py --repo /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench-Live
```

```
cd /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench-Live

git rev-parse HEAD
```

## Dataset Acquisition

Download datasets using each harness's recommended method. Record dataset version identifiers (tags/commit hashes) in the final report.

- SWE-bench Multilingual dataset: `SWE-bench/SWE-bench_Multilingual`
- SWE-bench-Live MultiLang dataset: `SWE-bench-Live/MultiLang`

## vLLM Serving

Use the exact serve commands from the vLLM section below. Start one model at a time, and only proceed to the next model after both suites complete.

### ⚠️ DGX Spark Unified Memory Constraints

**CRITICAL**: DGX Spark (GB10 with Grace CPU) uses unified memory where GPU and system RAM share the same 128GB pool. By default, vLLM allocates ALL available GPU memory for KV cache, consuming nearly all system RAM and causing OOM crashes.

**Required vLLM parameters** (discovered via investigation in Jan 2026):
- `--max-model-len 65536`: Limits context to 64K tokens
- `--gpu-memory-utilization 0.80`: Provides better headroom on UMA than 0.85
- `--max-num-seqs 1`: Limits concurrent sequences for single-agent evaluation

Without these parameters, vLLM consumes ~104GB leaving only ~4GB for system operations, causing crashes during agent evaluation. With these parameters: model weights (~29GB) + KV cache (~70GB) + system (~11GB) = ~110GB stable usage.

See the memory notes in this runbook for details.

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
  --gpu-memory-utilization 0.80 \
  --max-num-seqs 1
```

## Evaluation Runs

For each model, run both suites in order:

1. SWE-bench Multilingual (verified split)
2. SWE-bench-Live MultiLang (verified split)

### Generate Predictions via vLLM

Use `scripts/swebench_generate_predictions.py` to generate patch predictions from the vLLM OpenAI-compatible endpoint. The script sanitizes patches by default (strips code fences and trims whitespace) and writes both `model_patch` and `pred_patch` for compatibility with both harnesses. Activate the SWE-bench venv first:

```
source /home/sailorjoe6/Code/swebench-eval/work/swebench/.venv/bin/activate
```

SWE-bench Multilingual (JSONL output for `swebench.harness.run_evaluation`):

```
python scripts/swebench_generate_predictions.py \
  --suite swebench-multilingual \
  --model "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --output /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-multilingual/qwen3-predictions.jsonl
```

SWE-bench-Live MultiLang (JSON mapping for `evaluation.evaluation`):

```
python scripts/swebench_generate_predictions.py \
  --suite swebench-live-multilang \
  --model "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
  --output /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-live-multilang/qwen3-predictions.json
```

Use `--max-instances` for a short smoke test and `--dry-run` to validate output formatting without calling the API.
Use `--no-sanitize-diff` only if you need raw model output for debugging.

### Run Evaluations

Capture logs for each run in:

```
logs/<suite>/<model>/<run_id>/
```

Record any flags or deviations (Docker vs native, max model length, trust-remote-code, etc.).

#### SWE-bench Multilingual (SWE-bench harness)

Run the evaluation from the SWE-bench harness repo (installed editable). The harness requires a `run_id` and will
write `evaluation_results/` plus `logs/run_evaluation/` under the current working directory.

```
cd /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench

python -m swebench.harness.run_evaluation \
  --dataset_name SWE-bench/SWE-bench_Multilingual \
  --split test \
  --predictions_path /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-multilingual/qwen3-predictions.jsonl \
  --max_workers 8 \
  --run_id qwen3-swebench-multilingual \
  --report_dir /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-multilingual/reports
```

After each run, copy logs/results into the repo logs directory:

```
rsync -a --delete \
  /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench/logs/run_evaluation/qwen3-swebench-multilingual/ \
  logs/swebench-multilingual/qwen3/qwen3-swebench-multilingual/

rsync -a --delete \
  /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench/evaluation_results/ \
  logs/swebench-multilingual/qwen3/qwen3-swebench-multilingual/evaluation_results/
```

Adjust `--max_workers` for available CPU capacity.

#### SWE-bench-Live MultiLang (SWE-bench-Live harness)

Run the evaluation from the SWE-bench-Live repo. MultiLang uses per-language splits, so run each split and store
outputs separately. The harness writes results into the provided `--output_dir`.

```
cd /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench-Live

for split in c cpp go js rust java ts cs; do
  python -m evaluation.evaluation \
    --dataset SWE-bench-Live/MultiLang \
    --split "${split}" \
    --platform linux \
    --patch_dir /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-live-multilang/qwen3-predictions.json \
    --output_dir /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-live-multilang/results/qwen3/"${split}" \
    --workers 10 \
    --overwrite 0
done
```

Copy results into the repo logs directory:

```
rsync -a --delete \
  /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-live-multilang/results/qwen3/ \
  logs/swebench-live-multilang/qwen3/
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

Use the report template at `docs/SWE_BENCH_MULTILINGUAL_REPORT_TEMPLATE.md`.

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
  --swebench-report /home/sailorjoe6/Code/swebench-eval/work/swebench/SWE-bench/Qwen__Qwen3-Coder-30B-A3B-Instruct-FP8.qwen3-swebench-multilingual.json \
  --live-results-root /home/sailorjoe6/Code/swebench-eval/work/swebench/runs/swebench-live-multilang/results/qwen3 \
  --format markdown
```

Use `--output <path>` to save JSON or markdown into the run directory for later reporting.

## Notes and Deviations

If any suite cannot be run in Docker, document the exact reason and the native execution steps used.
