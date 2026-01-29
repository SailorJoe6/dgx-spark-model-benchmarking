# Multilingual SWE-Bench Agentic Evaluation for Coding Models on DGX Spark
**Specification**
**Date:** 2026-01-27
**Owner:** Joe

---

## 1. Purpose

Evaluate code-focused LLMs on multilingual, repo-level software engineering tasks using SWE-bench datasets with an agentic framework. The goal is to measure each model's ability to solve complex coding tasks across multiple languages using **mini-swe-agent**, an iterative agent that can explore codebases, run commands, and iterate on failures.

This spec defines what to run, in what order, which datasets to use, and how to record results. It does **not** provide a step-by-step execution plan.

### 1.1 Evaluation Approach

Models will be evaluated using **mini-swe-agent**, an agentic framework that:
- Operates in an iterative loop with bash-only tools
- Can explore codebases, run commands, and receive feedback
- Uses linear message history (no custom tool-calling interface)
- Framework: [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) (~100 line agent)
- Configuration: [OpenAutoCoder/live-swe-agent](https://github.com/OpenAutoCoder/live-swe-agent) (`config/livesweagent.yaml`)
- Reported to achieve >74% on SWE-bench Verified with frontier models (e.g., GPT-4, Claude)

**Relationship**: mini-swe-agent is a highly configurable framework. live-swe-agent is a separate repository containing optimized configuration files for mini-swe-agent. We will explicitly configure mini-swe-agent to use the `livesweagent.yaml` configuration from the live-swe-agent repo.

**Note**: This spec represents a pivot from the previous dual-framework approach. All prior direct inference results are discarded, and we are starting fresh with agentic evaluation only.

---

## 2. Current State

### 2.1 Infrastructure
- DGX Spark environment is operational with aarch64 architecture
- vLLM container image established: `nvcr.io/nvidia/vllm:25.12.post1-py3`
- Docker Hub authentication configured with local pull-through cache at `http://127.0.0.1:5000`
- amd64 emulation enabled via binfmt for running SWE-bench evaluation containers
- Python virtual environment exists at `/home/sailorjoe6/work/swebench/.venv`

### 2.2 Models
All models are downloaded and cached locally in `~/Models/huggingface`:
- `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`
- `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
- `MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ`
- `openai/gpt-oss-120b`

### 2.3 Datasets
Datasets downloaded to HuggingFace cache:
- `SWE-bench/SWE-bench_Multilingual` (split: `test`, 300 instances, HF sha `2b7aced941b4873e9cad3e76abbae93f481d1beb`)
- `SWE-bench-Live/MultiLang` (8 splits: c, cpp, go, js, rust, java, ts, cs; 413 total instances, HF sha `3430730b50bba3ad11b40ca9ba5b224f4034ce1a`)

### 2.4 Existing Resources
- HuggingFace token available at `~/.cache/huggingface/token`
- Work directory at `/home/sailorjoe6/work/swebench` contains:
  - Legacy harness clones (SWE-bench, SWE-bench-Live) - may be repurposed or archived
  - Existing venv with `datasets==4.5.0`
- Repository contains legacy scripts in `scripts/`:
  - `swebench_generate_predictions.py`
  - `swebench_report_metrics.py`
  - `swebench_pull_images.py`
  - `swebench_live_prepare.py`
  - **Action required**: Audit these scripts for relevance to agentic workflow; remove or repurpose as needed

### 2.5 Starting Fresh
- All existing outputs in `ralph/logs/swebench/` will be cleared before starting agentic evaluations
- All existing beads issues related to the prior workflow will be closed and archived
- Prior direct inference results (Qwen3: 0.67% and 7.3%) are discarded

---

## 3. Target Models

Evaluate in this exact order:

1. `Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8`
2. `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct`
3. `MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ`
4. `openai/gpt-oss-120b`

### 3.1 vLLM Serving Commands

All models must be served using `nvcr.io/nvidia/vllm:25.12.post1-py3` at `http://localhost:8000/v1`.

**⚠️ DGX Spark Unified Memory Constraints:**

The DGX Spark (GB10 with Grace CPU) uses **unified memory** where GPU and system RAM share the same physical memory pool (128GB total). By default, vLLM allocates ALL available GPU memory for KV cache, which on unified memory systems means consuming nearly all system RAM.

**Required vLLM parameters for DGX Spark:**
- `--max-model-len 65536`: Limits context length to 64K tokens (per NVIDIA guidance)
- `--gpu-memory-utilization 0.85`: Prevents vLLM from consuming all system memory
- `--max-num-seqs 1`: Limits concurrent sequences for single-agent evaluation

**Memory breakdown with these settings:**
- Model weights: ~29 GB (varies by model)
- KV cache: ~70 GB (at 0.85 utilization)
- Available for system: ~11 GB
- Total: ~110 GB used / 119 GB total

Without these limits, vLLM would consume ~104GB+ leaving only ~4GB for system operations, causing OOM events during agent evaluation.

Use the following commands:

**Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8**
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

**deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct**
```bash
docker run -d --name vllm-deepseek-lite --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct" \
    --trust-remote-code \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 1
```

**MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ**
```bash
docker run -d --name vllm-mixtral-awq --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ" \
    --quantization awq \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 1
```

**openai/gpt-oss-120b**
```bash
docker run -d --name vllm-gptoss --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "openai/gpt-oss-120b" \
    --max-model-len 65536 \
    --gpu-memory-utilization 0.85 \
    --max-num-seqs 1
```

---

## 4. Evaluation Framework: mini-swe-agent

### 4.1 Installation

Clone mini-swe-agent from source and install in the existing venv:
```bash
cd /home/sailorjoe6/work/swebench
git clone https://github.com/SWE-agent/mini-swe-agent.git
cd mini-swe-agent
source /home/sailorjoe6/work/swebench/.venv/bin/activate
pip install -e .
# Record commit hash for reporting
git rev-parse HEAD > /tmp/mini-swe-agent-commit.txt
```

**Rationale for source installation**: Allows inspection and extension of dataset handling, particularly for SWE-bench-Live MultiLang's 8 language splits.

### 4.2 Configuration

Clone live-swe-agent repository to obtain configuration files:
```bash
cd /home/sailorjoe6/work/swebench
git clone https://github.com/OpenAutoCoder/live-swe-agent.git
cd live-swe-agent
# Record commit hash for reporting
git rev-parse HEAD > /tmp/live-swe-agent-commit.txt
```

We will use `config/livesweagent.yaml` as the base configuration and modify it for local vLLM endpoints. This configuration will be passed to mini-swe-agent via the `--config` parameter:

```yaml
model:
  model_name: "hosted_vllm/<model-name>"  # e.g., "hosted_vllm/Qwen3-Coder-30B-A3B-Instruct-FP8"
  model_kwargs:
    api_base: "http://localhost:8000/v1"
  cost_tracking: "ignore_errors"  # or create model registry with 0.0 costs
```

**Note**: Model names are case-sensitive and must match the vLLM server's model identifier.

### 4.3 mini-swe-agent Fork Enhancements

We maintain a fork at `git@github.com:SailorJoe6/mini-swe-agent.git` with the following enhancements:

**1. Streaming Mode (`models/litellm_model.py`)**
- Prevents HTTP read timeouts on long vLLM generations
- Streams tokens client-side as they arrive
- Enabled by default via `streaming: true` in config

**2. Step Limit Warnings (`agents/default.py`)**
- At 90% of step limit: Warning to wrap up
- At final step: Urgent "MUST submit NOW" message
- Reduces LimitsExceeded exits by prompting timely submission

**3. Live Trajectory Streaming (`agents/default.py`, `run/utils/save.py`)**
- Streams agent messages to JSONL file in real-time
- Monitor with: `tail -f <instance_id>.traj.jsonl | jq .`
- JSONL automatically cleaned up after final trajectory is saved

**4. SWE-bench-Live/MultiLang Support (`run/extra/swebench.py`)**
- Fixed `get_swebench_docker_image_name()` to use `docker_image` field
- Enables support for SWE-bench-Live/MultiLang dataset

### 4.4 Batch Evaluation

mini-swe-agent provides built-in batch evaluation via `mini-extra swebench`:

**For SWE-bench Multilingual:**
```bash
mini-extra swebench \
  --model "hosted_vllm/<model-name>" \
  --config /path/to/livesweagent.yaml \
  --subset multilingual \
  --split test \
  --workers 1 \
  --output /path/to/results
```

**For SWE-bench-Live MultiLang:**
Run 8 separate invocations (one per language split):
```bash
for split in c cpp go js rust java ts cs; do
  mini-extra swebench \
    --model "hosted_vllm/<model-name>" \
    --config /path/to/livesweagent.yaml \
    --subset live-multilang \
    --split $split \
    --workers 1 \
    --output /path/to/results/$split
done
```

**✅ RESOLVED:** SWE-bench-Live/MultiLang is supported via our fork (see Section 4.3 item 4). Use the HuggingFace dataset path directly:
```bash
mini-extra swebench \
  --config /path/to/config.yaml \
  --subset "SWE-bench-Live/MultiLang" \
  --split c \
  --workers 1 \
  --output /path/to/results
```

### 4.5 Parallelism Settings

**🚨 CRITICAL: Only ONE agent at a time, ALWAYS sequential 🚨**

- **Agent generation**: `--workers 1` (sequential execution, NEVER concurrent)
  - **Rationale**: DGX Spark vLLM server **cannot handle concurrent LLM requests**
  - **Constraint**: Insufficient system memory for multiple agents
  - **Meaning**: ONE agent process runs, processing instance 1, completes, then instance 2, completes, etc. (serial within single agent run)
  - **NEVER**: Multiple concurrent agent processes running at the same time
  - **NEVER**: Multiple vLLM instances running at the same time
  - **ALWAYS**: `--workers 1` in all mini-swe-agent commands
  - **Clarification**: When we say "run 10 instances," this means ONE `mini-extra swebench` command that processes 10 instances sequentially, NOT 10 separate concurrent commands

- **Test evaluation**: Pipelined with agent generation, memory-aware parallelism
  - **Timing**: Start evaluation for a split immediately AFTER that split's agent generation completes
  - **Pipelining**: While agent generates patches for split N+1, evaluation runs on split N
  - **Workload**: CPU-bound test execution, no LLM inference (does not compete with GPU)

  **Worker strategy depends on vLLM state:**

  | Mode | vLLM Status | Available Memory | Recommended Workers |
  |------|-------------|------------------|---------------------|
  | Pipelined | Running (~104GB) | ~15GB | `--workers 1` only |
  | Post-agent | Stopped | ~100GB+ | `--workers 8-10` |

  - **During pipelined mode**: vLLM consumes most system memory; use `--workers 1` to avoid crashes
  - **After agent runs complete**: Stop vLLM, reclaim memory, use aggressive parallelism
  - **Rationale**: Pipelining reduces wall-clock time; conservative workers during pipeline prevent crashes

---

## 5. Evaluation Suites

Two multilingual SWE-bench datasets must be evaluated:

### 5.1 SWE-bench Multilingual
- **Dataset**: `SWE-bench/SWE-bench_Multilingual`
- **Split**: `test`
- **Instances**: 300
- **HF sha**: `2b7aced941b4873e9cad3e76abbae93f481d1beb`

### 5.2 SWE-bench-Live MultiLang
- **Dataset**: `SWE-bench-Live/MultiLang`
- **Splits**: 8 language splits (c, cpp, go, js, rust, java, ts, cs)
- **Instances**: 413 total (c=31, cpp=17, go=68, js=75, rust=45, java=62, ts=87, cs=28)
- **HF sha**: `3430730b50bba3ad11b40ca9ba5b224f4034ce1a`

---

## 6. Execution Requirements

### 6.1 Environment Setup

- **Platform**: aarch64 (DGX Spark) with `DOCKER_DEFAULT_PLATFORM=linux/amd64` for SWE-bench evaluation containers
- **amd64 emulation**: Already enabled via binfmt/QEMU
- **Docker Hub**: Already authenticated with local pull-through cache at `http://127.0.0.1:5000`
- **HuggingFace token**: Available at `~/.cache/huggingface/token`

### 6.2 Evaluation Workflow

For each model (in order):

1. **Clear prior outputs**: Remove existing results from `ralph/logs/swebench/<suite>/<model>/`
2. **Start vLLM server**: Use the model-specific docker command from Section 3.1
3. **Verify endpoint**: Ensure `http://localhost:8000/v1/models` responds
4. **Run SWE-bench Multilingual**:
   - Execute `mini-extra swebench` with `--subset multilingual --split test --workers 1`
   - Agent generates patches (sequential, one instance at a time)
   - mini-swe-agent outputs `preds.json`
   - After agent completes, run evaluation harness (see Section 6.2.1 for worker strategy)
   - Save results to `ralph/logs/swebench/swebench-multilingual/<model>/`
5. **Run SWE-bench-Live MultiLang (Pipelined)**:
   - Execute splits sequentially with pipelined evaluation:
     ```
     Agent: [C split] → [cpp split] → [go split] → ... → [cs split]
     Eval:        [C eval] → [cpp eval] → [go eval] → ... → [cs eval]
     ```
   - When agent completes split N, immediately start evaluation for split N
   - Agent continues to split N+1 while evaluation runs on split N
   - Save results to `ralph/logs/swebench/swebench-live-multilang/<model>/<split>/`
6. **Stop vLLM server**: `docker stop <container-name> && docker rm <container-name>`
7. **Record metrics**: Extract pass rates, solved counts, and errors from evaluation outputs

### 6.2.1 Test Evaluation Worker Strategy

**⚠️ Memory-Aware Parallelism**

DGX Spark's unified memory architecture is sensitive to memory pressure. The system will freeze or crash if memory is exhausted.

**Two operating modes:**

**Mode 1: Pipelined (vLLM running)**
- vLLM consumes ~104GB of 119GB system memory
- Only ~15GB available for evaluation containers
- **MUST use `--workers 1`** - no exceptions
- Monitor: `watch -n 5 'free -h'` - pause if available <10GB

**Mode 2: Post-Agent (vLLM stopped)**
- After all agent splits complete, stop vLLM: `docker stop vllm-qwen3-optimized`
- ~100GB+ memory becomes available
- Can safely use `--workers 8` or `--workers 10`
- Use this mode to catch up on any remaining evaluations

**Evaluation command template:**
```bash
cd ~/work/swebench/SWE-bench-Live
python -m evaluation.evaluation \
  --dataset SWE-bench-Live/MultiLang \
  --split <lang> \
  --platform linux \
  --patch_dir <path-to-preds.json> \
  --output_dir <output-path> \
  --workers 1 \      # Use 1 during pipelined mode, 8-10 after vLLM stops
  --overwrite 0
```

### 6.3 Error Handling

- **Blockers**: Log a beads issue, attempt to fix within a timeboxed effort, document in the plan if unresolved
- **Instance failures**: Continue evaluation, document affected instances in the final report's "Known Limitations" section
- **Environmental issues**: Document transparently (e.g., Go runtime crashes, Docker emulation issues)

---

## 7. Results & Reporting

### 7.1 Output Structure

Results must be organized as:
```
ralph/logs/swebench/
  swebench-multilingual/
    qwen3/
    deepseek/
    mixtral/
    gptoss/
  swebench-live-multilang/
    qwen3/
      c/, cpp/, go/, js/, rust/, java/, ts/, cs/
    deepseek/
      c/, cpp/, go/, js/, rust/, java/, ts/, cs/
    mixtral/
      c/, cpp/, go/, js/, rust/, java/, ts/, cs/
    gptoss/
      c/, cpp/, go/, js/, rust/, java/, ts/, cs/
```

### 7.2 Final Report

A single markdown report must be produced at `ralph/plans/AGENTIC_EVALUATION_REPORT.md` (or similar name focusing on agentic results).

**Required sections:**

1. **Executive Summary**
   - Brief overview of agentic evaluation results
   - Key findings across all models and datasets

2. **Overview Table**
   - Model × Dataset results
   - Columns: Model, Dataset, Total Tasks, Solved, Pass Rate

3. **Per-Model Sections**
   - Subsection for each model (Qwen3, DeepSeek, Mixtral, GPT-OSS)
   - Results for SWE-bench Multilingual (300 instances)
   - Results for SWE-bench-Live MultiLang (413 instances, breakdown by language split)
   - Notable patterns, errors, or insights

4. **Environment Notes**
   - vLLM container tag: `nvcr.io/nvidia/vllm:25.12.post1-py3`
   - mini-swe-agent commit hash
   - live-swe-agent commit hash
   - Dataset versions (HF shas)
   - HuggingFace cache path: `~/Models/huggingface`
   - Platform: aarch64 with amd64 emulation via QEMU/binfmt
   - Docker configuration: authenticated, local pull-through cache enabled

5. **Known Limitations**
   - **Go runtime crashes**: Document instances affected by `fatal error: taggedPointerPack` (QEMU incompatibility)
   - **Environmental issues**: Platform-specific failures (not model failures)
   - **Affected instances**: List instance IDs that could not be evaluated
   - **Mitigation attempts**: What was tried to resolve issues
   - **Impact on results**: Percentage of instances affected
   - **Transparency note**: Clear statement that these are environmental, not model limitations

### 7.3 Minimum Metrics

For each model × dataset combination, report:
- Total instances
- Instances solved (passed tests)
- Pass rate (percentage)
- Errors by category (patch application failures, runtime crashes, etc.)

---

## 8. Assumptions & Constraints

- **Runtime**: No time constraint; full evaluation runs expected regardless of duration
- **Parallelism**: Sequential agent generation (1 worker), parallel test evaluation (10 workers)
- **Repeatability**: Workflow must be fully reproducible for each model
- **Resources**: Models cached locally, datasets downloaded, HF token available
- **Priority**: Models must be run in the specified order (Qwen3 → DeepSeek → Mixtral → GPT-OSS)
- **Memory monitoring**: System memory must be monitored during runs (see Section 8.1)

### 8.1 DGX Spark UMA Memory Architecture

**Important Platform Characteristic:**

DGX Spark uses a **Unified Memory Architecture (UMA)**, which enables dynamic memory sharing between the GPU and CPU. With many applications still updating to take advantage of UMA, you may encounter memory issues even when within the memory capacity of DGX Spark.

**UMA Buffer Cache Flushing:**

If memory issues occur, flush the buffer cache with:
```bash
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
```

*Source: [nvidia/vllm/README.md](../../nvidia/vllm/README.md) - DGX Spark vLLM playbook troubleshooting section*

This buffer cache flushing may be necessary between sequential evaluation runs to prevent memory accumulation in the UMA shared buffer.

**One-Time Setup for Passwordless Cache Flushing (Required for Automation):**

To enable cache flushing in automated scripts without password prompts:

```bash
# Create sudoers rule (one-time setup)
sudo visudo -f /etc/sudoers.d/drop-caches
```

Add this single line (replace `sailorjoe6` with your username):
```
sailorjoe6 ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
```

Save and exit. Test with:
```bash
echo 3 | sudo -n tee /proc/sys/vm/drop_caches > /dev/null && echo "✓ Setup successful"
```

### 8.2 Known Issue: System Reboot During Evaluation (2026-01-28)

**⚠️ INVESTIGATION INCOMPLETE - CONTROLLED TESTING REQUIRED**: See [`ralph/logs/swebench/memory-investigation.md`](../../logs/swebench/memory-investigation.md) for incident documentation.

**Incident Summary**: During the first SWE-bench-Live/MultiLang C split evaluation on 2026-01-28, the DGX Spark evaluation stopped after 2/31 instances and the system rebooted ~9 minutes later.

**Timeline**:
| Time | Event |
|------|-------|
| 02:17:29 | mini-swe-agent started C split (31 instances) |
| 02:20:18 | Completed instance 1: `samtools__samtools-2235` |
| 02:21:28 | Completed instance 2: `micropython__micropython-17683` |
| 02:21:28 | **Evaluation stopped** (log ended abruptly, no error) |
| 02:30:12 | **System rebooted cleanly** (intentional systemd reboot, not crash) |

**Investigation Findings**:
- This was **NOT** a crash, OOM event, or kernel panic
- System performed a clean, intentional reboot via systemd
- Root cause inconclusive due to lack of memory monitoring data
- After reboot, WiFi failed to connect and required manual intervention (WiFi is only network connection)
- No vLLM process logs found
- Same stopping pattern as previously reported incident (stopped after 2 instances)
- This was a SECOND incident; manager had rebooted after first incident

**Suspected Causes**:
1. **UMA Buffer Cache Accumulation** (Primary Hypothesis - see Section 8.1): Buffer cache may accumulate between sequential instances without proper flushing
2. Resource exhaustion (memory or CPU) causing system unresponsiveness, followed by manual or automatic reboot decision

**Required Actions** ⚠️ **PARTIALLY COMPLETE**:
- [x] Add memory monitoring infrastructure (monitor_memory.sh created)
- [x] Investigation report started (incident documented, but no controlled test data)
- [ ] 🔴 **CRITICAL**: Run controlled tests WITH MONITORING (Phase 3.4.2-3.4.4 of EXECUTION_PLAN.md)
- [ ] Test UMA buffer cache flushing between instances as potential mitigation (see Section 8.1)
- [ ] Establish resource baseline and safe operating parameters
- [ ] Complete investigation before ANY evaluations can resume

**🚨 BEFORE ANY TESTING: Memory monitoring MUST be started first:**
```bash
cd /home/sailorjoe6/work/swebench && ./scripts/monitor_memory.sh &
```

---

## 9. Out of Scope

- Direct inference evaluation (discarded)
- HumanEval-XL or other codegen-only benchmarks
- Performance benchmarking beyond pass rates
- Model weight modifications or custom quantization
- Two-Spark or distributed inference setups
- Framework comparison analysis (no baseline to compare against)

---

## 10. Definition of Done

Work is complete when:

1. All 4 models evaluated on both SWE-bench Multilingual (300 instances) and SWE-bench-Live MultiLang (413 instances across 8 splits)
2. Results captured in structured logs at `ralph/logs/swebench/<suite>/<model>/`
3. Final markdown report written at `ralph/plans/AGENTIC_EVALUATION_REPORT.md` (or similar)
4. Report includes all required sections: overview, per-model results, environment notes, known limitations
5. Legacy scripts audited (removed, repurposed, or documented as unused)
6. All existing beads issues related to old workflow closed
7. All changes committed and pushed to remote repository
