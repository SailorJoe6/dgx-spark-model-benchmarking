# Multilingual SWE-Bench Agentic Evaluation - Execution Plan

**Date:** 2026-01-27
**Owner:** Joe
**Spec Reference:** [SPECIFICATION.md](SPECIFICATION.md)

---

## 📦 Project Repository

**Canonical Location:** `git@github.com:SailorJoe6/dgx-spark-model-benchmarking.git`

All scripts, configs, tests, and documentation for this project live in the above repository.
This plan and spec are symlinked from the local checkout.

**Related Repositories:**
- **mini-swe-agent fork:** `git@github.com:SailorJoe6/mini-swe-agent.git` (streaming support)
- **Upstream mini-swe-agent:** `https://github.com/SWE-agent/mini-swe-agent.git`

**Local Checkout:**
```
~/Code/dgx-spark-playbooks/swebench-eval/  # Main project files
~/work/swebench/                           # Runtime environment
├── .venv/                                 # Python virtualenv
├── mini-swe-agent/                        # Forked agent (origin → SailorJoe6)
├── SWE-bench-Live/                        # Benchmark framework
├── configs/ → swebench-eval/configs/      # Symlink to project configs
├── scripts/ → swebench-eval/scripts/      # Symlink to project scripts
└── runs/                                  # Evaluation logs
```

---

## 🚀 Quick Start (For New Engineer)

**Goal**: Run Qwen3 evaluation on SWE-bench-Live/MultiLang (413 instances, 8 language splits)

**Current Beads Issue**: `dgx-spark-playbooks-zyl` (IN_PROGRESS)

**System Ready**:
- ✅ vLLM running at http://localhost:8000/v1 with Qwen3 model
- ✅ Memory monitoring active (2 processes)
- ✅ Config file verified at `/home/sailorjoe6/work/swebench/configs/qwen3-livesweagent.yaml`
- ✅ Output directories created (empty, ready for predictions)

**Execute**:
```bash
cd /home/sailorjoe6/work/swebench
source .venv/bin/activate

for split in c cpp go js rust java ts cs; do
  mini-extra swebench \
    --config configs/qwen3-livesweagent.yaml \
    --subset "SWE-bench-Live/MultiLang" \
    --split $split \
    --workers 1 \
    --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/$split/
done
```

**⚠️ DO NOT** add `--model` flag - it overrides config and causes model name mismatch errors.

See beads issue `dgx-spark-playbooks-zyl` for detailed context and monitoring commands.

---

## 🔄 Current Status (2026-01-29 00:30 UTC)

**Phase 1: Cleanup & Preparation** - ❌ NOT STARTED
- All tasks unchecked (see lines 48-118)
- Note: Cleanup can happen after evaluations complete; not blocking progress

**Phase 2: Framework Installation** - ✅ **COMPLETE**
- 2.1 mini-swe-agent: ✅ Complete
- 2.2 live-swe-agent: ✅ Complete
- 2.3 Dataset support: ✅ Complete
- 2.4 Model configs: ✅ **COMPLETE** (all 4 configs created and validated)
  - `qwen3-livesweagent.yaml` ✅
  - `deepseek-livesweagent.yaml` ✅ (created 2026-01-28)
  - `mixtral-livesweagent.yaml` ✅ (created 2026-01-28)
  - `gptoss-livesweagent.yaml` ✅ (created 2026-01-28)
  - All configs validated: YAML syntax, required fields, submission command fix, format_error fix, timeout_template
  - Tests: `tests/test_swebench_configs.py` (11 tests, all passing)

**Phase 3: Batch Evaluation System** - ✅ **COMPLETE**
- 3.1 Output directories: ✅ Created (all 8 splits for qwen3)
- 3.2 Evaluation scripts: ✅ Not needed (using mini-extra swebench directly)
- 3.3 Beads issues: ✅ Created (dgx-spark-playbooks-zyl exists, in_progress)
- 3.4 Memory Investigation: ✅ **COMPLETE** (beads issue closed)
  - Root cause: vLLM default KV cache allocated ~104GB, leaving only ~4GB
  - Fix: Added `--max-model-len 65536 --gpu-memory-utilization 0.85 --max-num-seqs 1`
  - Verified: Tests with 1 and 2 instances showed stable memory (~108GB, no accumulation)
  - SPECIFICATION.md updated with required vLLM parameters
  - **Git repository fix applied**: Added `cwd: "/testbed"` to config (2026-01-28)
  - Verified: Test instance now generates valid git diff patches

**Phase 4: Model Evaluations** - 🔄 **IN PROGRESS**
- 4.1 Qwen3 Evaluation: **RUNNING** with optimized config (beads: dgx-spark-playbooks-zyl)
  - ✅ C split COMPLETE: 31/31 instances, 28 patches, 3 context errors
  - 🔄 C++ split IN PROGRESS: 17 instances (started 2026-01-29 13:32 UTC)
  - ⏳ Remaining splits (go, js, rust, java, ts, cs): Queued

  **C Split Final Results (--max-model-len 262144 optimized, completed 2026-01-29 09:30 UTC):**
  | Metric | Value |
  |--------|-------|
  | Total instances | 31 |
  | Agent submitted (patch generated) | 28 |
  | ContextWindowExceededError | 3 (DynamoRIO__dynamorio-7583, valkey-io__valkey-2277, others) |
  | Submission rate | 90.3% |
  | OOM kills | 0 |
  | **Test pass/fail** | **NOT YET EVALUATED** (requires harness run) |

  **C Split Baseline Results (--max-model-len 65536, archived 2026-01-28 14:10 UTC):**
  | Metric | Value |
  |--------|-------|
  | Total instances | 31 |
  | Agent submitted (patch generated) | 30 |
  | ContextWindowExceededError | 1 (DynamoRIO__dynamorio-7561) |
  | Submission rate | 96.8% |
  | OOM kills | 0 |
  | **Test pass/fail** | **NOT YET EVALUATED** (requires harness run) |

  Note: These are agent completion metrics, not test evaluation results.
  Actual pass/fail rates require running `evaluation.evaluation` harness afterward.
  Baseline archived at `qwen3-c-baseline/` for comparison after all evaluations complete.

- 4.1.1 Qwen3 C-Split Experiment (Optimized): ✅ **COMPLETE** (streaming fix applied)
  - Goal: Re-run C split only with optimized vLLM params, compare to baseline
  - **Result: NO OOM** → Using optimized config for all remaining evaluations
  - **Final Status (2026-01-29 09:30 UTC)**:
    - Streaming fix implemented and tested (see Section 4.1.2)
    - Unit tests: 7/7 passing (`tests/test_litellm_streaming.py`)
    - Progress: **31/31 completed** ✅
    - Memory stable throughout: ~104GB used, ~15GB available
    - Log: `runs/qwen3-optimized-c-streaming-20260128-*.log`
    - **Context window hits**: 3 instances exceeded 256K limit
      - DynamoRIO__dynamorio-7583: Model degeneration (see note below)
      - Others: valkey-io__valkey-2277, zmkfirmware__zmk-2942
      - All saved trajectories gracefully, no crashes
    - **Note on DynamoRIO__dynamorio-7583 (beads dgx-spark-playbooks-uvh - CLOSED)**:
      - Investigation revealed model degeneration, NOT productive work
      - Model generated 85,759 repeated `</parameter>` tags in single API call
      - Consumed 1.1MB (~262K tokens) of garbage output
      - **Baseline (65K) succeeded** on this same instance (36 API calls, proper submission)
      - Larger context window may trigger different/unstable model behavior
      - Recommendation: Consider adding `max_tokens` limit to config

  **Optimized vLLM Parameters:**
  - `--max-model-len 262144` (256K, was 65536)
  - `--gpu-memory-utilization 0.80` (was 0.85)
  - `--kv-cache-dtype fp8_e4m3` (new)
  - `--max-num-seqs 1` (unchanged)

  **Archived Baseline Results:**
  - Location: `/home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3-c-baseline/`
  - Contains: 31 trajectory files + preds.json from original config run
  - Purpose: Compare pass/fail rates between baseline (65K) and optimized (256K) configs

  **Recovery Plan (if OOM):**
  1. Restore archived baseline C split from `qwen3-c-baseline/`
  2. Restart vLLM with original params (65536, 0.85)
  3. Resume evaluation from C++ split onward

  **Decision (2026-01-29): ✅ USING OPTIMIZED CONFIG**
  - Optimized config had NO OOM events
  - Submission rate: 90.3% (28/31) vs baseline 96.8% (30/31)
  - Trade-off: Slightly lower submission rate due to more context window hits
  - BUT: 256K context allows deeper reasoning on complex instances
  - **Decision:** Use optimized config for all remaining evaluations

  **Current Evaluation Status:**
  1. ✅ C split complete with optimized config (28/31 patches)
  2. 🔄 cpp split in progress (17 instances)
  3. ⏳ Remaining: go, js, rust, java, ts, cs (queued)
  4. Same config will be used for all 4 models (Qwen3, DeepSeek, Mixtral, GPT-OSS)

  **Adaptive Context Window Strategy (if using optimized config):**
  If ANY future evaluation causes an OOM kill after adopting the optimized config:
  1. Reduce `--max-model-len` by 16384 (16K) tokens
  2. Restart vLLM with reduced context window
  3. Retry the failed evaluation
  4. Repeat until either:
     - (a) All tests complete with no further OOM kills → **SUCCESS**
     - (b) Context window reaches 32768 (32K) and still OOM → **PROJECT BLOCKED**

  **Context Window Reduction Ladder:**
  ```
  262144 (256K) → OOM → reduce to:
  245760 (240K) → OOM → reduce to:
  229376 (224K) → OOM → reduce to:
  ...
  49152  (48K)  → OOM → reduce to:
  32768  (32K)  → OOM → PROJECT FAILURE (blocked)
  ```

  If we reach 32K and still experience OOM, the DGX Spark unified memory architecture
  cannot support these evaluations, and the project is considered blocked.

  **Post-Experiment Comparison (after all evaluations complete):**
  Run the SWE-bench-Live evaluation harness on BOTH C split result sets to compare actual pass/fail rates:
  1. Baseline (65K): `qwen3-c-baseline/preds.json`
  2. Optimized (256K): `qwen3/c/preds.json`

  ```bash
  # Evaluate baseline C split
  cd ~/work/swebench/SWE-bench-Live
  python -m evaluation.evaluation \
    --dataset SWE-bench-Live/MultiLang --split c --platform linux \
    --patch_dir /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3-c-baseline/preds.json \
    --output_dir ~/work/swebench/runs/swebench-live-multilang/eval-results/qwen3-baseline-c

  # Evaluate optimized C split
  python -m evaluation.evaluation \
    --dataset SWE-bench-Live/MultiLang --split c --platform linux \
    --patch_dir /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/c/preds.json \
    --output_dir ~/work/swebench/runs/swebench-live-multilang/eval-results/qwen3-optimized-c
  ```

  This comparison will show whether the larger context window (256K) improves actual test pass rates,
  not just agent completion rates.

### 4.1.2 API Timeout Issue and Streaming Fix

**Problem Discovered (2026-01-28 20:00 UTC):**
During Phase 4.1.1 experiment, the agent began hitting repeated API timeouts on complex instances
(e.g., DynamoRIO__dynamorio-7583). The instance was stuck in a retry loop for ~2 hours.

**Root Cause Analysis:**
1. vLLM was actively generating at ~40 tokens/s (GPU at 100% utilization)
2. Some instances require very long responses (40K+ tokens, taking >10 minutes)
3. The OpenAI client (used by litellm) has a default **read timeout of 600 seconds** (10 min)
4. When the timeout fires, the HTTP connection closes, litellm raises `APITimeoutError`
5. mini-swe-agent retries (up to 10 times with exponential backoff)
6. Each retry sends a **NEW request** - vLLM starts generating from scratch
7. Result: Wasted GPU cycles repeatedly generating the same long response

**Timeout Chain:**
```
OpenAI client default: Timeout(connect=5.0, read=600, write=600, pool=600)
                                          ^^^
                                    This is the culprit
```

**Why env vars don't help:**
- `LITELLM_REQUEST_TIMEOUT` and `OPENAI_TIMEOUT` are read at import time
- Cannot affect an already-running process
- Would require restart to take effect

**Solution Options Evaluated:**

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| 1. Increase timeout | Add `timeout: 1800` to model_kwargs | Simple config change | Arbitrary limit, may still be exceeded |
| 2. Streaming mode | Modify litellm_model.py to use streaming | Robust - tokens flow continuously, no timeout | Requires code change |

**Chosen Solution: Streaming Mode (Option 2)**

With streaming enabled:
- HTTP connection stays alive as tokens stream in
- No read timeout because data is continuously received
- Agent accumulates chunks and returns complete response
- No wasted GPU cycles on retries

**Implementation:**
Patch `mini-swe-agent/src/minisweagent/models/litellm_model.py`:

```python
# Before (non-streaming):
def _query(self, messages, **kwargs):
    return litellm.completion(
        model=self.config.model_name,
        messages=messages,
        **(self.config.model_kwargs | kwargs)
    )

# After (streaming):
def _query(self, messages, **kwargs):
    response = litellm.completion(
        model=self.config.model_name,
        messages=messages,
        stream=True,  # Enable streaming
        **(self.config.model_kwargs | kwargs)
    )
    # Accumulate streamed chunks
    chunks = list(response)
    # Reconstruct response object from chunks
    return self._reconstruct_response_from_chunks(chunks)
```

**Testing:**
- Unit test: Verify streaming accumulation works correctly
- Integration test: Run a single instance with known long response time
- Verify: No timeout errors, response matches expected format

**Files Modified:**
- `~/work/swebench/mini-swe-agent/src/minisweagent/models/litellm_model.py`

**Implementation Status: ✅ COMPLETE (2026-01-28 20:30 UTC)**
- Added `use_streaming` config option (default: true, env: `MSWEA_USE_STREAMING`)
- Added `_reconstruct_response_from_stream()` method to accumulate chunks
- Modified `_query()` to use streaming when enabled
- Tests: `tests/test_litellm_streaming.py` (7 tests, all passing)
- Integration test: Single instance completed successfully with streaming

**Rollback Plan:**
If streaming causes issues, set `MSWEA_USE_STREAMING=false` or revert code and use `timeout: 3600` in config.

**Phase 5-6: Reporting & Cleanup** - ❌ NOT STARTED

### 🔀 Pipelined Evaluation Strategy (Added 2026-01-29)

**Objective:** Reduce total wall-clock time by running test evaluation in parallel with agent generation.

**Key Insight:** Agent generation is GPU-bound (vLLM), while test evaluation is CPU-bound (Docker containers running tests). These workloads don't compete for the same resources.

**Pipeline Workflow:**
```
Agent:    [C split ────────────] [cpp split ───────] [go split ───────] ...
Test Eval:              [C eval ────] [cpp eval ────] [go eval ────] ...
```

- When agent completes split N, immediately start test evaluation for split N
- Agent continues to split N+1 while evaluation runs on split N
- Both run simultaneously without GPU contention

**Memory-Safe Worker Strategy:**

**While vLLM is running (pipelined mode):**
- vLLM consumes ~104GB of 119GB total memory
- ~15GB available for test evaluation containers
- **Recommended: `--workers 2`** (observed stable with 15GB headroom)
- Conservative fallback: `--workers 1` if memory pressure observed
- Monitor memory: `watch -n 5 'free -h'` - ensure >10GB available
- If memory drops <10GB available, reduce workers or pause evaluation

**Note:** Worker count cannot be changed on a running evaluation process.
Start with `--workers 2` for future splits; fall back to 1 if issues arise.

**After vLLM stops (post-agent mode):**
- Once all agent runs complete and vLLM container is stopped
- ~100GB+ memory becomes available
- Can safely use `--workers 8` or `--workers 10` for faster evaluation
- Still monitor memory, but much more headroom available

**⚠️ CRITICAL**: DGX Spark will freeze/crash under memory pressure. The conservative approach during pipelined mode is essential for system stability.

**Test Evaluation Command:**
```bash
cd ~/work/swebench && source .venv/bin/activate && cd SWE-bench-Live
nohup python -m evaluation.evaluation \
  --dataset SWE-bench-Live/MultiLang \
  --split <lang> \
  --platform linux \
  --patch_dir /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/<split>/preds.json \
  --output_dir ~/work/swebench/runs/swebench-live-multilang/eval-results/qwen3/<split> \
  --workers 2 \
  --overwrite 0 > ~/work/swebench/runs/eval-<split>-$(date +%Y%m%d-%H%M%S).log 2>&1 &
```

**🖥️ Infrastructure Status (2026-01-29 00:30 UTC):**

✅ **vLLM Server**: Running (OPTIMIZED CONFIG for experiment)
- Model: Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
- Endpoint: http://localhost:8000/v1
- Parameters: `--max-model-len 65536 --gpu-memory-utilization 0.85 --max-num-seqs 1`
- Status: Serving requests (verified with curl)

✅ **Memory Monitoring**: 2 processes active
- Process 1: PID 12365 (started 04:30)
- Process 2: PID 61815 (started 05:16)
- Logs: /home/sailorjoe6/work/swebench/runs/memory-monitor-*.log

✅ **Evaluation Process**: Running in background
- Main process: bash loop for all 8 splits
- Current: cpp split (17 instances)
- Log: /home/sailorjoe6/work/swebench/runs/qwen3-remaining-*.log

**⚠️ CRITICAL: Long-Running Evaluations Must Use `nohup`**

Evaluations can take 10+ hours per language split. To ensure they survive session disconnects,
system reboots, or terminal closures, ALWAYS use `nohup` when starting evaluation loops:

```bash
cd /home/sailorjoe6/work/swebench
source .venv/bin/activate
nohup /path/to/evaluation_script.sh > logs/evaluation-$(date +%Y%m%d-%H%M%S).log 2>&1 &
echo "Started with PID: $!"
```

**Why This Matters:**
- Regular `&` background processes die when the parent session closes
- System updates or reboots require restarting evaluations manually
- `nohup` ensures processes continue running regardless of session state

**Monitoring a nohup process:**
```bash
# Check if running
ps aux | grep mini-extra | grep -v grep

# Watch log output
tail -f /home/sailorjoe6/work/swebench/runs/qwen3-remaining-*.log

# Check split progress (count completed instances)
ls -la ralph/logs/swebench/swebench-live-multilang/qwen3/cpp/ | wc -l
```

✅ **Output Directories**: All 8 splits created
- Path: /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/{c,cpp,go,js,rust,java,ts,cs}/
- Status: Ready to receive predictions

✅ **Config File**: Verified correct
- Path: /home/sailorjoe6/work/swebench/configs/qwen3-livesweagent.yaml
- Model: hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
- Submission command: Fixed (includes git add -A && git diff --cached)
- Working directory: /testbed (correct)

**📊 Monitoring Commands:**

Monitor real-time progress:
```bash
# Watch evaluation output
tail -f /home/sailorjoe6/work/swebench/runs/qwen3-live-c-20260128-125343.log

# Check progress between splits
tail -f /home/sailorjoe6/work/swebench/runs/qwen3-all-splits-progress.log

# Monitor system memory
watch -n 60 'free -h'

# Check process status
ps aux | grep mini-extra

# Check for generated predictions
find /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/ -name "preds.json" -ls
```

---

## Overview

This execution plan provides step-by-step instructions for implementing the agentic evaluation workflow defined in [SPECIFICATION.md](SPECIFICATION.md). The plan represents a complete pivot from the previous direct inference approach to an agentic-only evaluation using mini-swe-agent.

**Key Changes from Prior Work:**
- Discarding all direct inference results and infrastructure
- Starting fresh with agentic framework (mini-swe-agent)
- **Extending mini-swe-agent to support SWE-bench-Live/MultiLang** (required)
- Closing all old beads issues related to dual-framework approach
- Clearing existing logs to start with clean slate

---

## Phase 1: Cleanup & Preparation

### 1.1 Close Old Workflow

**Objective:** Archive all artifacts and issues from the discarded direct inference approach.

**Tasks:**
- [ ] Close beads issue `dgx-spark-playbooks-a20` with reason explaining pivot to agentic-only
- [ ] Clear all existing outputs in `ralph/logs/swebench/` (backup first if needed)
  ```bash
  # Backup first (optional)
  tar -czf /home/sailorjoe6/work/swebench/logs-backup-$(date +%Y%m%d).tar.gz ralph/logs/swebench/
  # Clear
  rm -rf ralph/logs/swebench/*
  ```
- [ ] Audit legacy scripts in `scripts/` directory:
  - `swebench_generate_predictions.py` - Direct inference, not needed for agentic
  - `swebench_live_prepare.py` - May have dataset utilities, review
  - `swebench_pull_images.py` - Docker image management, may be useful
  - `swebench_report_metrics.py` - Metrics extraction, may be useful
- [ ] Decision: Archive, remove, or repurpose each legacy script
  - Suggested: Move to `scripts/archive/direct-inference/` for reference

**Success Criteria:**
- Old beads issue closed
- `ralph/logs/swebench/` is empty
- Legacy scripts audited and decision documented

### 1.2 Verify Environment Prerequisites

**Objective:** Confirm all infrastructure is ready for agentic evaluation.

**Tasks:**
- [ ] Verify Python venv exists: `/home/sailorjoe6/work/swebench/.venv`
  ```bash
  source /home/sailorjoe6/work/swebench/.venv/bin/activate
  python --version  # Should be Python 3.x
  pip list | grep datasets  # Should show datasets==4.5.0 or similar
  ```
- [ ] Verify Docker is running and authenticated
  ```bash
  docker info
  docker pull hello-world  # Test pull through cache
  ```
- [ ] Verify vLLM container image is available locally
  ```bash
  docker images | grep "nvcr.io/nvidia/vllm:25.12.post1-py3"
  ```
- [ ] Verify amd64 emulation is enabled
  ```bash
  ls /proc/sys/fs/binfmt_misc/qemu-x86_64
  ```
- [ ] Verify HuggingFace token exists
  ```bash
  test -f ~/.cache/huggingface/token && echo "HF token found"
  ```
- [ ] Verify all models are cached locally
  ```bash
  ls -lh ~/Models/huggingface/hub/ | grep -E "Qwen3-Coder-30B|DeepSeek-Coder-V2-Lite|Mixtral-8x22B|gpt-oss-120b"
  ```
- [ ] Verify datasets are cached
  ```bash
  python -c "from datasets import load_dataset; print(load_dataset('SWE-bench/SWE-bench_Multilingual', split='test').num_rows)"
  python -c "from datasets import load_dataset; ds = load_dataset('SWE-bench-Live/MultiLang'); print({k: len(v) for k, v in ds.items()})"
  ```

**Success Criteria:**
- All prerequisites verified and documented
- No blockers found
- Environment ready for framework installation

---

## Phase 2: Framework Installation

### 2.1 Install mini-swe-agent

**Objective:** Clone and install mini-swe-agent from source.

**Tasks:**
- [x] Clone mini-swe-agent repository ✅ (2026-01-28)
  ```bash
  cd /home/sailorjoe6/work/swebench
  git clone https://github.com/SWE-agent/mini-swe-agent.git
  cd mini-swe-agent
  ```
- [x] Record commit hash for reporting ✅ (d494d973f763245215abf9f85ba512c54ba6628c)
  ```bash
  git rev-parse HEAD > /tmp/mini-swe-agent-commit.txt
  cat /tmp/mini-swe-agent-commit.txt
  ```
- [x] Install in editable mode ✅ (mini-swe-agent v1.17.3)
  ```bash
  source /home/sailorjoe6/work/swebench/.venv/bin/activate
  pip install -e .
  ```
- [x] Verify installation ✅
  ```bash
  mini-extra --help
  which mini-extra
  ```
- [x] Test basic functionality ✅
  ```bash
  mini-extra swebench --help
  ```

**Success Criteria:**
- ✅ Repository cloned successfully
- ✅ Commit hash recorded: d494d973f763245215abf9f85ba512c54ba6628c
- ✅ `mini-extra` command available in venv
- ✅ Basic help commands work

### 2.2 Clone live-swe-agent (Configuration Source)

**Objective:** Clone live-swe-agent repository to obtain configuration files.

**Note**: live-swe-agent is NOT a dependency of mini-swe-agent. It's a separate repository containing optimized configuration files that we will pass to mini-swe-agent via the `--config` parameter.

**Tasks:**
- [x] Clone live-swe-agent repository ✅ (2026-01-28)
  ```bash
  cd /home/sailorjoe6/work/swebench
  git clone https://github.com/OpenAutoCoder/live-swe-agent.git
  cd live-swe-agent
  ```
- [x] Record commit hash for reporting ✅ (8d7dd8634580d1e09320b4c27d70380bc9ae74a8)
  ```bash
  git rev-parse HEAD > /tmp/live-swe-agent-commit.txt
  cat /tmp/live-swe-agent-commit.txt
  ```
- [x] Verify config file exists ✅
  ```bash
  test -f config/livesweagent.yaml && echo "Config file found"
  cat config/livesweagent.yaml  # Review structure
  ```

**Success Criteria:**
- ✅ Repository cloned successfully
- ✅ Commit hash recorded: 8d7dd8634580d1e09320b4c27d70380bc9ae74a8
- ✅ `config/livesweagent.yaml` exists and reviewed

### 2.3 Investigate and Extend mini-swe-agent for SWE-bench-Live/MultiLang Support

**Objective:** Determine if mini-swe-agent supports SWE-bench-Live/MultiLang, and extend if needed.

**⚠️ RESOLVED (2026-01-28):** mini-swe-agent supports SWE-bench-Live/MultiLang **out-of-the-box** using the HuggingFace dataset path directly.

**🔧 CRITICAL FIX APPLIED (2026-01-28):** While dataset loading works, there was a bug in mini-swe-agent's `get_swebench_docker_image_name()` function. The SWE-bench-Live/MultiLang dataset uses the field `docker_image` instead of `image_name` used by original SWE-bench datasets.

**Fix Applied to `/home/sailorjoe6/work/swebench/mini-swe-agent/src/minisweagent/run/extra/swebench.py`:**
```python
# Changed from:
image_name = instance.get("image_name", None)
# To:
image_name = instance.get("image_name") or instance.get("docker_image")
```

This allows mini-swe-agent to correctly use Docker images from SWE-bench-Live/MultiLang (e.g., `starryzhang/sweb.eval.x86_64.samtools_1776_samtools-2235`).

**Investigation Results:**

The `--subset` parameter accepts either:
1. A predefined alias (e.g., `lite`, `multilingual`, `verified`)
2. A full HuggingFace dataset path (e.g., `SWE-bench-Live/MultiLang`)

mini-swe-agent's DATASET_MAPPING includes:
```python
DATASET_MAPPING = {
    "full": "princeton-nlp/SWE-Bench",
    "verified": "princeton-nlp/SWE-Bench_Verified",
    "lite": "princeton-nlp/SWE-Bench_Lite",
    "multimodal": "princeton-nlp/SWE-Bench_Multimodal",
    "multilingual": "swe-bench/SWE-Bench_Multilingual",
    "smith": "SWE-bench/SWE-smith",
    "_test": "klieret/swe-bench-dummy-test-dataset",
}
```

For datasets not in this mapping, mini-swe-agent falls back to using the subset parameter as a HuggingFace dataset path directly.

**Tasks:**

- [x] **Inspect existing dataset handling code** ✅
  - Found: `src/minisweagent/run/extra/swebench.py` contains DATASET_MAPPING
  - Key code: `dataset_path = DATASET_MAPPING.get(subset, subset)` - falls back to using subset as path

- [x] **Test if SWE-bench-Live/MultiLang already works** ✅
  - Confirmed: `--subset "SWE-bench-Live/MultiLang" --split c` loads successfully
  - Dataset loaded: 31 instances for c split
  - Dataset schema verified: includes `problem_statement`, `patch`, `docker_image`, etc.

- [x] **Decision Point: Does it work out-of-the-box?** ✅
  - **YES!** No extension needed. Use `--subset "SWE-bench-Live/MultiLang" --split <lang>`

- [N/A] ~~**[IF NEEDED] Understand current architecture**~~ (Not needed)

- [N/A] ~~**[IF NEEDED] Implement SWE-bench-Live/MultiLang support**~~ (Not needed)

- [x] **Usage documentation** ✅
  For SWE-bench-Live/MultiLang, use:
  ```bash
  mini-extra swebench \
    --subset "SWE-bench-Live/MultiLang" \
    --split <lang>  # c, cpp, go, js, rust, java, ts, cs
    --model "hosted_vllm/<model-id>" \
    --config /path/to/config.yaml \
    --workers 1 \
    --output /path/to/output/
  ```

**Success Criteria:**
- ✅ Dataset loading code identified and understood
- ✅ Determined SWE-bench-Live/MultiLang works out-of-the-box (no extension needed)
- ✅ `--subset "SWE-bench-Live/MultiLang" --split <lang>` works for all 8 languages
- ✅ Test instance can be loaded from c split (31 instances)
- ✅ Approach documented for reporting
- ✅ **BLOCKER CLEARED:** Ready for Phase 4 (Model Evaluations)

### 2.4 Configure mini-swe-agent for Local vLLM

**Objective:** Create model-specific configuration files based on live-swe-agent's `livesweagent.yaml`, modified to point to our local vLLM endpoint.

**Tasks:**
- [x] Create config directory in work area ✅ (2026-01-28)
  ```bash
  mkdir -p /home/sailorjoe6/work/swebench/configs
  ```
- [x] Create 4 model-specific configs based on `live-swe-agent/config/livesweagent.yaml` ✅ (all 4 created 2026-01-28)
  - [x] `qwen3-livesweagent.yaml` ✅ (with all fixes applied)
  - [x] `deepseek-livesweagent.yaml` ✅ (created 2026-01-28, all fixes applied)
  - [x] `mixtral-livesweagent.yaml` ✅ (created 2026-01-28, all fixes applied)
  - [x] `gptoss-livesweagent.yaml` ✅ (created 2026-01-28, all fixes applied)
- [x] Each config modifies the base `livesweagent.yaml` to specify: ✅ (for qwen3)
  ```yaml
  model:
    model_name: "hosted_vllm/<model-id>"
    cost_tracking: "ignore_errors"
    model_kwargs:
      api_base: "http://localhost:8000/v1"
  ```
  **Note:** Model names must match vLLM server identifiers exactly (case-sensitive)

- [x] **⚠️ CRITICAL: Apply submission command fix to ALL configs** ✅ (verified 2026-01-28)

  Each config MUST have the corrected submission instructions. The original `livesweagent.yaml` has a bug that causes empty patch submissions. When creating each new config:

  1. **In `instance_template`**, change submission instruction from:
     ```
     `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`. Do not combine it with any other command.
     ```
     To:
     ```
     ```bash
     echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached
     ```
     This command stages all your changes and outputs the patch.
     ```

  2. **In `format_error_template`**, change:
     ```
     `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` without any other command.
     ```
     To:
     ```
     `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached`
     ```

  **Reference:** Use `qwen3-livesweagent.yaml` as the template for all other configs.

- [x] Validate YAML syntax ✅ (all 4 configs validated, tests at `tests/test_swebench_configs.py`)
  ```bash
  python -m unittest tests.test_swebench_configs -v  # 11 tests, all passing
  ```

**🔧 Additional Config Fixes Applied (2026-01-28):**
1. Added `timeout_template` field (required by mini-swe-agent but missing from base config)
2. Removed Jinja2 template variables (`{{system}}`, `{{release}}`, etc.) that aren't available in Docker environment - replaced with hardcoded "Linux x86_64 (Docker container)"
3. Removed macOS-specific sed instructions (not applicable in Docker containers)
4. Added `cost_tracking: "ignore_errors"` under model section (required for local vLLM)

**🐛 CRITICAL BUG FIX: Empty Patch Submissions (2026-01-28)**

**Problem Discovered:** The 2 C split instances that completed before the system reboot (see [memory investigation](../logs/swebench/memory-investigation.md)) both submitted empty patches (`"model_patch": ""`), despite the agent making actual file edits.

**Root Cause Analysis:**

mini-swe-agent's `has_finished()` function in `agents/default.py:118-122` captures the submission as **whatever text comes AFTER** the `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` marker:

```python
def has_finished(self, output: dict[str, str]):
    lines = output.get("output", "").lstrip().splitlines(keepends=True)
    if lines and lines[0].strip() in ["MINI_SWE_AGENT_FINAL_OUTPUT", "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"]:
        raise Submitted("".join(lines[1:]))  # <-- Takes text AFTER the marker
```

The **default mini-swe-agent config** (`swebench.yaml`) correctly instructs:
```bash
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached
```

But the **live-swe-agent config** (`livesweagent.yaml`) incorrectly instructs:
> `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` - Do not combine it with any other command.

This means when the agent runs just `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`, there's nothing after the marker, so the submission is empty.

**Evidence from Trajectories:**

| Instance | API Calls | Behavior | Result |
|----------|-----------|----------|--------|
| `micropython__micropython-17683` | 17 | Submitted with `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` alone | Empty patch |
| `samtools__samtools-2235` | 31 | Never issued submit command, just summarized work | Empty patch (session ended abnormally) |

**Fix Applied:**

Updated `qwen3-livesweagent.yaml` submission instructions:

```yaml
# BEFORE (broken):
6. Submit your changes and finish your work by issuing the following command: `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`.
   Do not combine it with any other command.

# AFTER (fixed):
6. Submit your changes and finish your work by issuing the following command:
   ```bash
   echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached
   ```
   This command stages all your changes and outputs the patch.
```

Also updated `format_error_template` to use the correct submission command.

**Impact:** All future evaluation runs will now correctly capture patches. Previous C split results are invalid and must be re-run.

**Success Criteria:**
- ✅ 4 of 4 config files created (qwen3, deepseek, mixtral, gptoss)
- ✅ YAML syntax validated for all 4 configs
- ✅ Configs reference correct vLLM endpoint
- ✅ All critical fixes applied (submission command, format_error, timeout_template)
- ✅ Tests created and passing: `tests/test_swebench_configs.py` (11 tests)

### 2.4.1 CRITICAL BUG FIX: Garbage Patch Submissions (2026-01-29)

**Problem Discovered:** During C split evaluation, 13 of 28 "submitted" patches were >50KB of garbage content (git warnings, test output, build logs) instead of valid git diffs. The largest was 6.4MB.

| Instance | "Patch" Size | Content |
|----------|-------------|---------|
| quickjs-ng__quickjs-1113 | 6.4 MB | Garbage |
| php__php-src-* (5 instances) | 1.4-3.0 MB | Garbage |
| samtools__samtools-2235 | 679 KB | Garbage |
| ... and 6 others | 52-325 KB | Garbage |

**Root Cause:** The submission command `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached` runs `git add -A` at submission time. This outputs warnings (submodules, embedded repos, large files) which get captured as part of the patch output, corrupting the submission.

**Solution: Two-Step Submission Process**

The agent must now submit in two separate commands:

**Step 1: Stage changes (separate command)**
```bash
git add -A
```
Agent reviews output for warnings/errors and fixes issues before proceeding.

**Step 2: Submit clean patch (separate command)**
```bash
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff --cached
```
Files are already staged, so this only outputs the clean diff.

**Config Change:**
```yaml
## Submission (Two-Step Process)

When you've completed your work, you MUST submit using this two-step process:

**Step 1: Stage your changes (separate command)**
git add -A
Review the output carefully for any warnings or errors.

**Step 2: Submit your patch (separate command, AFTER step 1)**
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff --cached

CRITICAL: Do NOT include `git add` in your submission command.
```

**Impact:** All configs updated. C split must be re-run with corrected configs.

### 2.4.2 Step Limit Improvements (2026-01-29)

**Problem Discovered:** During cpp split evaluation, 11 of 13 instances hit `LimitsExceeded` (250 step limit) without submitting. The agent ran out of steps before completing the task.

**Solution: Increased Limit + Warnings**

1. **Increased step_limit from 250 to 500** - More time for complex tasks

2. **Added step limit warnings in mini-swe-agent** (`agents/default.py`):
   - At **90% of steps** (450/500): Warning message to wrap up
   - At **final step** (500/500): Urgent "MUST submit NOW" message

**Warning at 90%:**
```
<WARNING>
⏰ RUNNING LOW ON STEPS: You have used 450/500 steps (50 remaining).
You should wrap up your work soon and submit your solution.
</WARNING>
```

**Warning at final step:**
```
<URGENT_WARNING>
⚠️ THIS IS YOUR FINAL STEP! You have used 500/500 steps.
You MUST submit your solution NOW.
</URGENT_WARNING>
```

**Code Location:** `mini-swe-agent/src/minisweagent/agents/default.py` - `_add_step_limit_warning()` method

**Impact:** Agents now have more time AND get warned before being cut off, reducing LimitsExceeded exits.

### 2.4.3 Live Trajectory Streaming (2026-01-29)

**Feature Added:** Real-time streaming of agent messages to a JSONL file for monitoring active evaluations.

**Note:** This is a feature for human operators to monitor long-running evaluations. The AI agent executing this plan does NOT need to use this feature - evaluations should be started with `nohup` and allowed to run to completion unattended.

**For Human Operators:** To monitor an active instance: `tail -f <instance_id>.traj.jsonl | jq .`

**Implementation Details:**

1. **New method in `DefaultAgent`**: `set_live_trajectory_path(path)`
   - Sets the destination for JSONL streaming
   - Creates parent directories and clears any existing file

2. **Modified `add_message()` method**:
   - Appends each message to the JSONL file as it's added to `self.messages`
   - Failures are silently ignored to prevent streaming issues from breaking the agent

3. **JSONL cleanup in `save_traj()`**:
   - After saving the final `.traj.json`, the temporary `.traj.jsonl` is deleted
   - Ensures only the final trajectory file remains after completion

4. **Integration in `swebench.py`**:
   - Calls `agent.set_live_trajectory_path(instance_dir / f"{instance_id}.traj.jsonl")` before running
   - Each instance streams to its own JSONL file while running

**Code Locations:**
- `mini-swe-agent/src/minisweagent/agents/default.py` - `set_live_trajectory_path()`, `add_message()`
- `mini-swe-agent/src/minisweagent/run/utils/save.py` - JSONL cleanup in `save_traj()`
- `mini-swe-agent/src/minisweagent/run/extra/swebench.py` - Integration call

**JSONL Format:**
Each line is a complete JSON object:
```json
{"role": "system", "content": "...", "timestamp": 1738171234.567}
{"role": "user", "content": "...", "timestamp": 1738171235.123}
{"role": "assistant", "content": "...", "timestamp": 1738171240.456}
```

**Impact:** Enables real-time monitoring of agent progress without waiting for the run to complete.

### 2.4.4 Streaming Mode for vLLM (2026-01-28)

**Problem:** vLLM generates very long responses (especially with extended thinking), causing HTTP read timeouts in the LiteLLM client.

**Solution:** Added streaming mode to `litellm_model.py` that streams tokens as they arrive, preventing timeouts.

**Implementation:**
- Enabled by default: `streaming: true` in model config
- Streaming accumulates tokens client-side until generation is complete
- Prevents `httpx.ReadTimeout` errors on long generations

**Code Location:** `mini-swe-agent/src/minisweagent/models/litellm_model.py` - `query()` method

**Config Setting:**
```yaml
model:
  streaming: true  # Enabled by default
```

**Impact:** Eliminates timeout errors during long vLLM generations.

---

## Phase 3: Batch Evaluation System

### 3.1 Create Output Directory Structure

**Objective:** Pre-create directories for organized result storage.

**Tasks:**
- [ ] Create output directory structure
  ```bash
  mkdir -p ralph/logs/swebench/swebench-multilingual/{qwen3,deepseek,mixtral,gptoss}
  mkdir -p ralph/logs/swebench/swebench-live-multilang/qwen3/{c,cpp,go,js,rust,java,ts,cs}
  mkdir -p ralph/logs/swebench/swebench-live-multilang/deepseek/{c,cpp,go,js,rust,java,ts,cs}
  mkdir -p ralph/logs/swebench/swebench-live-multilang/mixtral/{c,cpp,go,js,rust,java,ts,cs}
  mkdir -p ralph/logs/swebench/swebench-live-multilang/gptoss/{c,cpp,go,js,rust,java,ts,cs}
  ```
- [ ] Verify structure matches spec requirements (Section 7.1)

**Success Criteria:**
- Directory structure created
- Matches spec exactly

### 3.2 Create Evaluation Scripts

**Objective:** Build wrapper scripts for reproducible batch evaluation.

**Tasks:**
- [ ] Create `scripts/agentic/run_swebench_multilingual.sh`
  - Takes model name, config path, output directory as arguments
  - Runs `mini-extra swebench --subset multilingual --split test --workers 1`
  - Logs stdout/stderr to output directory
  - Records start/end times
  - Captures exit code
- [ ] Create `scripts/agentic/run_swebench_live_multilang.sh`
  - Takes model name, config path, output base directory as arguments
  - Loops through 8 language splits (c, cpp, go, js, rust, java, ts, cs)
  - Runs `mini-extra swebench --subset live-multilang --split <lang> --workers 1` for each
  - Saves results to `<output_base>/<lang>/`
  - Logs execution metadata
- [ ] Create `scripts/agentic/serve_vllm_model.sh`
  - Takes model identifier as argument
  - Maps to correct docker run command from spec Section 3.1
  - Starts vLLM container in detached mode
  - Waits for endpoint health check
  - Returns success/failure
- [ ] Create `scripts/agentic/stop_vllm_model.sh`
  - Stops and removes vLLM container
  - Confirms cleanup
- [ ] Make all scripts executable
  ```bash
  chmod +x scripts/agentic/*.sh
  ```

**Success Criteria:**
- 4 wrapper scripts created
- Scripts are parameterized and reusable
- All scripts executable
- Scripts tested with dry-run or simple examples

### 3.3 Create Beads Issues for Evaluation Work

**Objective:** Track evaluation work as structured beads issues.

**Tasks:**
- [ ] Create beads epic for overall evaluation
  ```bash
  bd create --title="Complete agentic SWE-bench multilingual evaluation for 4 models" \
    --type=feature --priority=1
  ```
- [ ] Create beads issues for each model (4 issues)
  - "Evaluate Qwen3-Coder-30B with mini-swe-agent" [task, P1]
  - "Evaluate DeepSeek-V2-Lite with mini-swe-agent" [task, P1]
  - "Evaluate Mixtral-8x22B with mini-swe-agent" [task, P1]
  - "Evaluate gpt-oss-120b with mini-swe-agent" [task, P1]
- [ ] Add dependencies (sequential execution)
  ```bash
  # Example: DeepSeek depends on Qwen3 completing
  bd dep add <deepseek-id> <qwen3-id>
  bd dep add <mixtral-id> <deepseek-id>
  bd dep add <gptoss-id> <mixtral-id>
  ```
- [ ] Create beads issue for final report
  - "Generate agentic evaluation final report" [task, P1]
  - Depends on all 4 model evaluations completing

**Success Criteria:**
- Epic and 5 beads issues created
- Dependencies configured correctly
- Issues are in `ready` state (or first one ready, rest blocked)

### 3.4 Memory Investigation (BLOCKING - Added 2026-01-28)

**Objective:** Investigate and resolve the system memory exhaustion that crashed the DGX Spark during SWE-bench-Live/MultiLang C split evaluation.

**Background:**
On 2026-01-28 at ~02:21, the system crashed after completing 2/31 C split instances. User observed:
- GPU utilization dropped normally after instance 2 completed
- System memory remained dangerously high (did not drop)
- System crashed before instance 3 could start
- This behavior was **NOT observed** with vanilla SWE-bench testing harness

**Primary Hypothesis:** DGX Spark uses Unified Memory Architecture (UMA) with dynamic memory sharing between GPU and CPU. The UMA buffer cache may accumulate between sequential instances without proper flushing, causing memory to remain high even after GPU releases memory.

**UMA Memory Management Context:**
> DGX Spark uses a Unified Memory Architecture (UMA), which enables dynamic memory sharing between the GPU and CPU. With many applications still updating to take advantage of UMA, you may encounter memory issues even when within the memory capacity of DGX Spark. If that happens, manually flush the buffer cache with:
> ```bash
> echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
> ```
> (Requires one-time passwordless sudo setup - see Section 3.4.4 Prerequisites)
>
> *Source: [nvidia/vllm/README.md](../../nvidia/vllm/README.md) - DGX Spark vLLM playbook*

**Tasks:**

**⚠️ CRITICAL CONSTRAINT - SEQUENTIAL EXECUTION ONLY ⚠️**

Throughout ALL testing in this investigation:
- **ONLY ONE vLLM instance** runs at any time (never multiple vLLM servers)
- **ONLY ONE agent instance** runs at any time (`--workers 1` ALWAYS)
- Agents run instances **SEQUENTIALLY** (one completes, then next starts)
- **NEVER concurrent/parallel agent execution** - DGX Spark lacks memory for this
- Parallel execution is ONLY for test evaluation phase (CPU-bound, after patches generated)

#### 3.4.1 Set Up Memory Monitoring
- [ ] Create memory monitoring script
  ```bash
  cat > /home/sailorjoe6/work/swebench/scripts/monitor_memory.sh << 'EOF'
  #!/bin/bash
  # Monitor system memory every 5 seconds, log to file
  LOG_FILE="${1:-/home/sailorjoe6/work/swebench/runs/memory-monitor-$(date +%Y%m%d-%H%M%S).log}"
  echo "Logging memory to: $LOG_FILE"
  while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $(free -h | grep Mem | awk '{print "Total:",$2,"Used:",$3,"Free:",$4,"Available:",$7}')" >> "$LOG_FILE"
    # Also log docker memory usage
    echo "$(date '+%Y-%m-%d %H:%M:%S') | Docker: $(docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}' 2>/dev/null | tail -n +2 | tr '\n' ' ')" >> "$LOG_FILE"
    sleep 5
  done
  EOF
  chmod +x /home/sailorjoe6/work/swebench/scripts/monitor_memory.sh
  ```
- [ ] Test monitoring script runs correctly in background
  ```bash
  /home/sailorjoe6/work/swebench/scripts/monitor_memory.sh &
  MONITOR_PID=$!
  sleep 30
  kill $MONITOR_PID
  cat /home/sailorjoe6/work/swebench/runs/memory-monitor-*.log | tail -10
  ```

#### 3.4.2 Baseline Memory Measurement

**🚨 CRITICAL: START MEMORY MONITORING FIRST 🚨**

**BEFORE ANY TESTING: Start the monitoring script and keep it running throughout ALL tests below:**
```bash
cd /home/sailorjoe6/work/swebench
./scripts/monitor_memory.sh &
MONITOR_PID=$!
echo "Memory monitor PID: $MONITOR_PID (keep this running for ALL tests)"
# Verify it's running
ps aux | grep monitor_memory.sh
```

**🚨 CRITICAL: SEQUENTIAL EXECUTION ONLY 🚨**

**This tests for memory ACCUMULATION between sequential instances, NOT concurrent execution!**
- DGX Spark can ONLY handle ONE agent at a time
- ONLY ONE vLLM instance at a time
- `--workers 1` ALWAYS (sequential, never concurrent)
- "Run N instances" means: ONE agent command that processes N instances one-after-another
- Agent runs instance 1, completes, then instance 2, completes, etc. (serial within single agent run)
- This tests if memory leaks/accumulates BETWEEN sequential runs
- **NEVER** means: Multiple concurrent agent processes running at the same time

**Test Procedure:**
- [ ] **START MEMORY MONITORING** (see above - MUST be running before proceeding)
- [ ] Start vLLM server for Qwen3 (if not already running)
- [ ] Record baseline memory with vLLM server running (NO agent active)
  ```bash
  # vLLM is running, NO agent active
  free -h
  docker stats --no-stream
  # Wait 30 seconds, record again to ensure stable baseline
  ```
- [ ] **Test 1: Run ONE agent command that processes 1 instance**, measure memory after completion
  - **Command**: ONE `mini-extra swebench` invocation with `--workers 1`
  - **Behavior**: Agent processes 1 instance, completes, exits
  - **Measure**: Does memory drop back to baseline after agent exits?
  - **NOT**: Running 1 concurrent agent (there's only ever 1 agent anyway!)

- [ ] **Test 2: Run ONE agent command that processes 2 instances sequentially**, measure memory after completion
  - **Command**: ONE `mini-extra swebench` invocation with `--workers 1` that processes 2 instances
  - **Behavior**: Agent processes instance 1, completes, then instance 2, completes, then exits
  - **Total instances**: 2 (processed one-after-another by single agent process)
  - **Measure**: Is memory higher than after Test 1? Did it accumulate between instances?
  - **NOT**: Running 2 concurrent agents (NEVER ALLOWED!)

- [ ] **Test 3: Run ONE agent command that processes 5 instances sequentially**, measure memory after completion
  - **Command**: ONE `mini-extra swebench` invocation with `--workers 1` that processes 5 instances
  - **Behavior**: Agent processes instances 1→2→3→4→5 sequentially, then exits
  - **Total instances**: 5 (processed one-after-another by single agent process)
  - **Measure**: Does memory keep growing with each additional sequential instance?
  - **NOT**: Running 5 concurrent agents (NEVER ALLOWED!)

- [ ] **STOP memory monitoring after tests complete**
  ```bash
  kill $MONITOR_PID
  # Review the memory log
  tail -100 /home/sailorjoe6/work/swebench/runs/memory-monitor-*.log
  ```

- [ ] Document findings:
  - Does memory grow with each sequential instance?
  - Does it recover between instances?
  - Is there a memory leak in mini-swe-agent's sequential execution?
  - Attach memory log excerpts showing the pattern

#### 3.4.3 Test UMA Buffer Cache Flushing (DGX Spark-Specific)

**🚨 START MEMORY MONITORING FIRST (if not already running) 🚨**

**Objective:** Test if manually flushing the UMA buffer cache between instances prevents memory accumulation.

**Rationale:** DGX Spark uses Unified Memory Architecture (UMA) with shared GPU/CPU memory. The buffer cache may retain data even after GPU releases memory. This is a platform-specific behavior that may not occur with vanilla SWE-bench harness on non-UMA systems.

**Prerequisites:**
- [ ] **One-time setup: Configure passwordless cache flushing**
  ```bash
  # Create sudoers rule (only needed once)
  sudo visudo -f /etc/sudoers.d/drop-caches
  ```
  Add this line (replace `sailorjoe6` with your username):
  ```
  sailorjoe6 ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
  ```
  Save and test:
  ```bash
  echo 3 | sudo -n tee /proc/sys/vm/drop_caches > /dev/null && echo "✓ Setup successful"
  ```

**Test Procedure:**
- [ ] **START memory monitoring** (if not already running from 3.4.2-3.4.3)
  ```bash
  cd /home/sailorjoe6/work/swebench
  ./scripts/monitor_memory.sh &
  MONITOR_PID=$!
  echo "Memory monitor PID: $MONITOR_PID"
  ```

- [ ] **Test with manual buffer cache flushing between instances:**
  ```bash
  # Run 1 instance
  mini-extra swebench \
    --model "hosted_vllm/Qwen3-Coder-30B-A3B-Instruct-FP8" \
    --config configs/qwen3-livesweagent.yaml \
    --subset "SWE-bench-Live/MultiLang" \
    --split c \
    --workers 1 \
    --instance-ids "samtools__samtools-2235" \
    --output /tmp/test-uma-flush/run1/

  # Flush UMA buffer cache (passwordless after setup)
  echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

  # Record memory after flush
  free -h

  # Run 2nd instance
  mini-extra swebench \
    --model "hosted_vllm/Qwen3-Coder-30B-A3B-Instruct-FP8" \
    --config configs/qwen3-livesweagent.yaml \
    --subset "SWE-bench-Live/MultiLang" \
    --split c \
    --workers 1 \
    --instance-ids "micropython__micropython-17683" \
    --output /tmp/test-uma-flush/run2/

  # Flush UMA buffer cache again
  echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

  # Record memory after flush
  free -h
  ```

- [ ] **Compare with baseline test from 3.4.2** (no flushing between instances)
  - Does manual flushing prevent memory accumulation?
  - Does memory return to baseline after flushing?
  - Is this a viable mitigation for sequential evaluations?

- [ ] **STOP memory monitoring**
  ```bash
  kill $MONITOR_PID
  # Review the memory log for comparison
  tail -100 /home/sailorjoe6/work/swebench/runs/memory-monitor-*.log
  ```

- [ ] **Document findings:**
  - Effect of UMA buffer cache flushing on memory levels
  - Whether this resolves the memory accumulation issue
  - Recommendation: integrate flushing into evaluation loop if effective

#### 3.4.4 Identify Memory Leak Source (If UMA Flushing Doesn't Resolve)

**Note:** Only proceed with this section if UMA buffer cache flushing (3.4.4) does NOT resolve the memory accumulation issue.

- [ ] Investigate Docker container cleanup
  ```bash
  # After mini-swe-agent run, check for orphaned containers
  docker ps -a | grep minisweagent
  # Check for orphaned volumes
  docker volume ls
  ```
- [ ] Investigate mini-swe-agent memory handling
  - [ ] Review `minisweagent/environment/docker.py` for container cleanup
  - [ ] Check if trajectory data is accumulating in memory
  - [ ] Check LiteLLM client-side caching behavior
- [ ] Investigate vLLM memory behavior
  - [ ] Does vLLM accumulate context between requests?
  - [ ] Check KV cache settings
- [ ] Investigate UMA-specific issues (if Section 3.4.4 tests inconclusive)
  - [ ] Check system logs for UMA-related warnings
  - [ ] Test if issue occurs with non-Docker workloads
  - [ ] Consult DGX Spark UMA documentation for known issues

#### 3.4.5 Document Findings
- [ ] Create investigation report at `ralph/logs/swebench/memory-investigation.md`
  - Root cause identified (or hypotheses if inconclusive)
  - Memory growth pattern documented
  - Comparison with vanilla harness
  - **UMA buffer cache behavior** and effectiveness of manual flushing
  - Recommended mitigations
- [ ] Update this execution plan with findings
- [ ] If root cause found: implement fix or workaround before resuming evaluations
  - If UMA flushing is effective: add flush commands between evaluation runs
  - Document flush procedure in evaluation workflow
- [ ] If inconclusive: define safe memory thresholds and automatic restart procedures

**Success Criteria:**
- Memory monitoring infrastructure in place
- Root cause identified OR safe operating parameters defined
- Documented comparison with vanilla SWE-bench harness
- **UMA buffer cache flushing tested** and effectiveness documented
- Clear go/no-go decision for resuming Phase 4 evaluations
- If proceeding: mitigation strategy defined (e.g., periodic UMA flushing, memory thresholds)

**⚠️ BLOCKING:** Phase 4 evaluations (SWE-bench-Live/MultiLang) cannot resume until this investigation is complete.

---

## Phase 4: Model Evaluations

**🚨 CRITICAL REQUIREMENT FOR ALL EVALUATIONS 🚨**

**BEFORE running ANY evaluation in this phase, memory monitoring MUST be active:**
```bash
cd /home/sailorjoe6/work/swebench && ./scripts/monitor_memory.sh &
```
Verify it's running: `ps aux | grep monitor_memory.sh`

**Without memory monitoring, we cannot diagnose system issues. This is non-negotiable.**

---

**Note:** Execute in exact order specified in spec Section 3.

### 4.1 Evaluate Qwen3-Coder-30B-A3B-Instruct-FP8

**Objective:** Run agentic evaluation for Qwen3 on both datasets.

**Pre-flight Checks:**
- [ ] Verify model cached: `~/Models/huggingface/hub/*Qwen3-Coder-30B*`
- [ ] Update beads issue to `in_progress`
- [ ] Confirm no other vLLM containers running
- [ ] **CRITICAL: Phase 3.4 Memory Investigation MUST be complete before proceeding**

**Execution Steps:**

1. **Start vLLM Server**
   ```bash
   docker run -d --name vllm-qwen3-coder --gpus all --ipc=host \
     --ulimit memlock=-1 --ulimit stack=67108864 \
     -p 8000:8000 \
     -v ~/Models/huggingface:/root/.cache/huggingface \
     -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
     -e HF_HOME=/root/.cache/huggingface \
     nvcr.io/nvidia/vllm:25.12.post1-py3 \
     vllm serve "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
   ```

2. **Verify Endpoint**
   ```bash
   # Wait for server to be ready (may take 2-5 minutes)
   sleep 120
   curl http://localhost:8000/v1/models
   ```

3. **Run SWE-bench Multilingual** ❌ NOT PROPERLY COMPLETED

   **Previous Attempt (2026-01-28) - INVALID:**
   - Ran without following proper Phase 1-3 setup
   - Only 17/300 instances completed (stopped prematurely)
   - 2 instances resolved (0.67% pass rate)
   - No proper output directory structure (Phase 3.1 not done)
   - No wrapper scripts (Phase 3.2 not done)
   - Results location unclear/unstructured
   - Beads issue `dgx-spark-playbooks-o4a` was INCORRECTLY closed

   **Must Re-run After:**
   - Phase 1: Cleanup complete
   - Phase 2.4: All configs created
   - Phase 3.1-3.3: Setup complete
   - Phase 3.4: Memory investigation complete

4. **Evaluate Predictions** - NOT APPLICABLE (Step 3 not properly completed)

5. **Run SWE-bench-Live MultiLang** ⚠️ **BLOCKED - Memory Investigation Required**

   **🔴 INCIDENT (2026-01-28 02:21):** System crashed during C split evaluation after completing 2/31 instances.

   **Observations:**
   - GPU utilization dropped normally after instance 2 completed
   - **System memory did NOT drop** - remained dangerously high
   - System crashed before instance 3 could start
   - This behavior was **NOT observed** with vanilla SWE-bench harness

   **Progress Lost:**
   - C split: 2/31 completed (samtools, micropython) - both submitted empty patches
   - Other splits (cpp, go, js, rust, java, ts, cs): Not started

   **🐛 Empty Patch Root Cause (Investigated 2026-01-28):**
   The empty patches were caused by a **config bug**, not the memory issue. See Phase 2.4 "CRITICAL BUG FIX: Empty Patch Submissions" for full details. The live-swe-agent config instructed the agent to run `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` alone, but mini-swe-agent expects `git diff` output after the marker to capture the patch. **Config has been fixed.** C split must be re-run from scratch with the corrected config.

   **⚠️ Phase 3.4 (Memory Investigation) Status:** ❌ **INCOMPLETE - CONTROLLED TESTING NOT DONE**
   - Incident documented at [`ralph/logs/swebench/memory-investigation.md`](../logs/swebench/memory-investigation.md)
   - Report conclusion: "Unable to determine root cause due to lack of memory monitoring"
   - **REQUIRED:** Complete sections 3.4.2-3.4.4 (controlled tests with monitoring) before ANY evaluations

   **Investigation Findings (2026-01-28):**
   - System rebooted cleanly at 02:30:34 (NOT a crash/OOM)
   - Evaluation stopped after 2/31 instances (matches previous pattern)
   - Root cause inconclusive due to lack of memory monitoring
   - Memory monitoring infrastructure now in place (monitor_memory.sh)

   **🚨 PRE-RESUME ACTIONS ABSOLUTELY REQUIRED 🚨**

   **DO NOT START EVALUATIONS WITHOUT COMPLETING ALL STEPS BELOW:**

   1. **🔴 CRITICAL - START MEMORY MONITORING FIRST:**
      ```bash
      cd /home/sailorjoe6/work/swebench
      ./scripts/monitor_memory.sh &
      echo "Memory monitor PID: $!"
      ```
      **This must run BEFORE any evaluation starts. Without this, we cannot diagnose future issues.**

   2. Clear invalid C split results:
      ```bash
      rm -rf /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/c/*
      ```

   3. Ensure corrected config is in place (submission command now includes `git diff`)
      - Config location: `/home/sailorjoe6/work/swebench/configs/qwen3-livesweagent.yaml`
      - Verify line contains: `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached`

   4. Verify vLLM is running:
      ```bash
      curl http://localhost:8000/v1/models
      ```

   5. **Run single-instance test before full evaluation** (see investigation report for details)

   **⚠️⚠️⚠️ BEFORE RUNNING THE COMMAND BELOW, VERIFY MEMORY MONITORING IS RUNNING ⚠️⚠️⚠️**

   Check that monitor_memory.sh is running:
   ```bash
   ps aux | grep monitor_memory.sh
   # Should show the monitoring script running
   # If NOT running, START IT NOW: cd /home/sailorjoe6/work/swebench && ./scripts/monitor_memory.sh &
   ```

   Full evaluation command (ONLY run after ALL pre-resume actions completed):
   ```bash
   # FIRST: Verify memory monitoring is running (see above)
   # SECOND: Run the evaluation
   for split in c cpp go js rust java ts cs; do
     echo "=== Running split: $split ==="
     mini-extra swebench \
       --model "hosted_vllm/Qwen3-Coder-30B-A3B-Instruct-FP8" \
       --config configs/qwen3-livesweagent.yaml \
       --subset "SWE-bench-Live/MultiLang" \
       --split $split \
       --workers 1 \
       --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/$split/ \
       2>&1 | tee /home/sailorjoe6/work/swebench/runs/qwen3-live-$split-$(date +%Y%m%d-%H%M%S).log
   done
   ```

6. **Stop vLLM Server**
   ```bash
   docker stop vllm-qwen3-coder
   docker rm vllm-qwen3-coder
   ```

7. **Record Metrics**
   - [ ] Extract pass rates from evaluation outputs
   - [ ] Count solved instances per dataset
   - [ ] Document any errors or environmental issues
   - [ ] Save summary to `ralph/logs/swebench/qwen3-summary.txt`

8. **Close Beads Issue**
   ```bash
   bd close <qwen3-issue-id>
   ```

**Success Criteria:**
- vLLM server started and verified
- Both datasets evaluated (300 + 413 instances)
- Results saved to correct directories
- Metrics extracted and documented
- Server stopped and cleaned up
- Beads issue closed

### 4.1.1 Re-test Qwen3 with Optimized vLLM Parameters (EXPERIMENTAL)

**Objective:** Re-evaluate Qwen3 on SWE-bench-Live/MultiLang with optimized vLLM configuration to test if longer context window and FP8 KV cache improve agent performance.

**Rationale:**
- **Increased context window** (65K → 256K): Allow agent to maintain more codebase context across iterations
- **Reduced memory utilization** (0.85 → 0.80): Provide more system memory headroom (~17GB vs ~11GB)
- **FP8 KV cache quantization**: Reduce KV cache memory footprint while maintaining quality
- **Goal**: Determine if agent solution quality improves with longer context

**Prerequisites:**
- [x] Current baseline evaluation (Phase 4.1) completed successfully with NO OOM events
- [x] Baseline results recorded for comparison
- [ ] System memory stable throughout baseline run
- [ ] Memory monitoring active

**Execution Steps:**

1. **Archive Baseline Results**
   ```bash
   # Create archive directory for baseline results
   mkdir -p /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3-baseline

   # Copy baseline results (from current run with --max-model-len 65536)
   cp -r /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/* \
        /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3-baseline/

   # Clear current results directory for re-test
   rm -rf /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/*
   ```

2. **Stop Current vLLM Server**
   ```bash
   docker stop vllm-qwen3-coder
   docker rm vllm-qwen3-coder
   ```

3. **Start vLLM Server with Optimized Parameters**
   ```bash
   docker run -d --name vllm-qwen3-coder-optimized --gpus all --ipc=host \
     --ulimit memlock=-1 --ulimit stack=67108864 \
     -p 8000:8000 \
     -v ~/Models/huggingface:/root/.cache/huggingface \
     -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
     -e HF_HOME=/root/.cache/huggingface \
     nvcr.io/nvidia/vllm:25.12.post1-py3 \
     vllm serve "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8" \
       --gpu-memory-utilization 0.80 \
       --max-model-len 262144 \
       --max-num-seqs 1 \
       --kv-cache-dtype fp8_e4m3
   ```

   **Parameter Changes:**
   - `--gpu-memory-utilization 0.80` (was 0.85): More headroom (~17GB free vs ~11GB)
   - `--max-model-len 262144` (was 65536): 4x larger context window (256K tokens)
   - `--kv-cache-dtype fp8_e4m3` (NEW): FP8 quantization for KV cache (reduces memory)

4. **Verify Endpoint**
   ```bash
   sleep 120
   curl http://localhost:8000/v1/models
   # Should show max_model_len: 262144
   ```

5. **Monitor Memory During Startup**
   ```bash
   # Check memory footprint is stable with new parameters
   free -h
   # If memory usage exceeds 110GB, consider reducing max-model-len further
   ```

6. **Run SWE-bench-Live MultiLang with Optimized Config**
   ```bash
   cd /home/sailorjoe6/work/swebench
   source .venv/bin/activate

   # Verify memory monitoring is active
   ps aux | grep monitor_memory.sh

   for split in c cpp go js rust java ts cs; do
     echo "=== Running split: $split (OPTIMIZED) at $(date) ==="
     mini-extra swebench \
       --config configs/qwen3-livesweagent.yaml \
       --subset "SWE-bench-Live/MultiLang" \
       --split $split \
       --workers 1 \
       --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/qwen3/$split/ \
       2>&1 | tee /home/sailorjoe6/work/swebench/runs/qwen3-optimized-live-$split-$(date +%Y%m%d-%H%M%S).log
   done
   ```

7. **Monitor for OOM Events**
   - [ ] Watch memory throughout run: `watch -n 60 'free -h'`
   - [ ] Check for any OOM kills: `dmesg | grep -i "out of memory"`
   - [ ] If OOM occurs, ABORT re-test and revert to baseline parameters
   - [ ] If stable, continue to completion

8. **Stop vLLM Server**
   ```bash
   docker stop vllm-qwen3-coder-optimized
   docker rm vllm-qwen3-coder-optimized
   ```

9. **Compare Results**
   ```bash
   # Extract metrics from both runs
   # Baseline: qwen3-baseline/
   # Optimized: qwen3/

   # Compare pass rates:
   # - Count solved instances in each run
   # - Calculate pass rate difference
   # - Identify which instances were solved in optimized but not baseline (and vice versa)
   # - Document in comparison report
   ```

10. **Document Findings**
    - [ ] Create comparison report: `ralph/logs/swebench/qwen3-optimization-comparison.md`
    - [ ] Include:
      - Memory usage comparison (baseline vs optimized)
      - Pass rate comparison (overall and per-language)
      - Instances solved uniquely by each configuration
      - Agent behavior differences (if observable from trajectories)
      - Recommendation: Keep optimized params or revert to baseline?
    - [ ] Update SPECIFICATION.md if optimized parameters prove superior

**Decision Point:**
- **If optimized config performs BETTER**: Use these parameters for remaining models (DeepSeek, Mixtral, GPT-OSS)
- **If optimized config performs SAME/WORSE**: Revert to baseline parameters for remaining models
- **If OOM occurs**: Document findings, use baseline parameters for remaining models

**Success Criteria:**
- Re-evaluation completes with NO OOM events
- Comparison report generated with clear metrics
- Decision made on which parameters to use for remaining models
- If optimized is better: Update Section 3.1 in SPECIFICATION.md with new recommended parameters

### 4.2 Evaluate DeepSeek-Coder-V2-Lite-Instruct

**Objective:** Run agentic evaluation for DeepSeek on both datasets.

**Pre-flight Checks:**
- [ ] Verify Qwen3 evaluation completed
- [ ] Verify model cached: `~/Models/huggingface/hub/*DeepSeek-Coder-V2-Lite*`
- [ ] Update beads issue to `in_progress`

**Execution Steps:**

1. **Start vLLM Server**
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
       --gpu-memory-utilization 0.85 \
       --max-model-len 32768
   ```

2. **Verify Endpoint**
   ```bash
   sleep 120
   curl http://localhost:8000/v1/models
   ```

3. **Run SWE-bench Multilingual**
   ```bash
   cd /home/sailorjoe6/work/swebench
   source .venv/bin/activate

   mini-extra swebench \
     --model "hosted_vllm/DeepSeek-Coder-V2-Lite-Instruct" \
     --config configs/deepseek-livesweagent.yaml \
     --subset multilingual \
     --split test \
     --workers 1 \
     --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-multilingual/deepseek/ \
     2>&1 | tee /home/sailorjoe6/work/swebench/runs/deepseek-multilingual-$(date +%Y%m%d-%H%M%S).log
   ```

4. **Run SWE-bench-Live MultiLang**
   ```bash
   for split in c cpp go js rust java ts cs; do
     echo "=== Running split: $split ==="
     mini-extra swebench \
       --model "hosted_vllm/DeepSeek-Coder-V2-Lite-Instruct" \
       --config configs/deepseek-livesweagent.yaml \
       --subset live-multilang \
       --split $split \
       --workers 1 \
       --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/deepseek/$split/ \
       2>&1 | tee /home/sailorjoe6/work/swebench/runs/deepseek-live-$split-$(date +%Y%m%d-%H%M%S).log
   done
   ```

5. **Stop vLLM Server**
   ```bash
   docker stop vllm-deepseek-lite
   docker rm vllm-deepseek-lite
   ```

6. **Record Metrics**
   - [ ] Extract metrics and save summary

7. **Close Beads Issue**
   ```bash
   bd close <deepseek-issue-id>
   ```

**Success Criteria:**
- Same as Qwen3 section

### 4.3 Evaluate Mixtral-8x22B-Instruct-v0.1-AWQ

**Objective:** Run agentic evaluation for Mixtral on both datasets.

**Pre-flight Checks:**
- [ ] Verify DeepSeek evaluation completed
- [ ] Verify model cached: `~/Models/huggingface/hub/*Mixtral-8x22B*`
- [ ] Update beads issue to `in_progress`

**Execution Steps:**

1. **Start vLLM Server**
   ```bash
   docker run -d --name vllm-mixtral-awq --gpus all --ipc=host \
     --ulimit memlock=-1 --ulimit stack=67108864 \
     -p 8000:8000 \
     -v ~/Models/huggingface:/root/.cache/huggingface \
     -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
     -e HF_HOME=/root/.cache/huggingface \
     nvcr.io/nvidia/vllm:25.12.post1-py3 \
     vllm serve "MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ" \
       --quantization awq
   ```

2. **Verify Endpoint**
   ```bash
   sleep 120
   curl http://localhost:8000/v1/models
   ```

3. **Run SWE-bench Multilingual**
   ```bash
   cd /home/sailorjoe6/work/swebench
   source .venv/bin/activate

   mini-extra swebench \
     --model "hosted_vllm/Mixtral-8x22B-Instruct-v0.1-AWQ" \
     --config configs/mixtral-livesweagent.yaml \
     --subset multilingual \
     --split test \
     --workers 1 \
     --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-multilingual/mixtral/ \
     2>&1 | tee /home/sailorjoe6/work/swebench/runs/mixtral-multilingual-$(date +%Y%m%d-%H%M%S).log
   ```

4. **Run SWE-bench-Live MultiLang**
   ```bash
   for split in c cpp go js rust java ts cs; do
     echo "=== Running split: $split ==="
     mini-extra swebench \
       --model "hosted_vllm/Mixtral-8x22B-Instruct-v0.1-AWQ" \
       --config configs/mixtral-livesweagent.yaml \
       --subset live-multilang \
       --split $split \
       --workers 1 \
       --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/mixtral/$split/ \
       2>&1 | tee /home/sailorjoe6/work/swebench/runs/mixtral-live-$split-$(date +%Y%m%d-%H%M%S).log
   done
   ```

5. **Stop vLLM Server**
   ```bash
   docker stop vllm-mixtral-awq
   docker rm vllm-mixtral-awq
   ```

6. **Record Metrics**
   - [ ] Extract metrics and save summary

7. **Close Beads Issue**
   ```bash
   bd close <mixtral-issue-id>
   ```

**Success Criteria:**
- Same as Qwen3 section

### 4.4 Evaluate openai/gpt-oss-120b

**Objective:** Run agentic evaluation for GPT-OSS on both datasets.

**Pre-flight Checks:**
- [ ] Verify Mixtral evaluation completed
- [ ] Verify model cached: `~/Models/huggingface/hub/*gpt-oss-120b*`
- [ ] Update beads issue to `in_progress`

**Execution Steps:**

1. **Start vLLM Server**
   ```bash
   docker run -d --name vllm-gptoss --gpus all --ipc=host \
     --ulimit memlock=-1 --ulimit stack=67108864 \
     -p 8000:8000 \
     -v ~/Models/huggingface:/root/.cache/huggingface \
     -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
     -e HF_HOME=/root/.cache/huggingface \
     nvcr.io/nvidia/vllm:25.12.post1-py3 \
     vllm serve "openai/gpt-oss-120b"
   ```

2. **Verify Endpoint**
   ```bash
   sleep 120
   curl http://localhost:8000/v1/models
   ```

3. **Run SWE-bench Multilingual**
   ```bash
   cd /home/sailorjoe6/work/swebench
   source .venv/bin/activate

   mini-extra swebench \
     --model "hosted_vllm/gpt-oss-120b" \
     --config configs/gptoss-livesweagent.yaml \
     --subset multilingual \
     --split test \
     --workers 1 \
     --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-multilingual/gptoss/ \
     2>&1 | tee /home/sailorjoe6/work/swebench/runs/gptoss-multilingual-$(date +%Y%m%d-%H%M%S).log
   ```

4. **Run SWE-bench-Live MultiLang**
   ```bash
   for split in c cpp go js rust java ts cs; do
     echo "=== Running split: $split ==="
     mini-extra swebench \
       --model "hosted_vllm/gpt-oss-120b" \
       --config configs/gptoss-livesweagent.yaml \
       --subset live-multilang \
       --split $split \
       --workers 1 \
       --output /home/sailorjoe6/Code/dgx-spark-playbooks/ralph/logs/swebench/swebench-live-multilang/gptoss/$split/ \
       2>&1 | tee /home/sailorjoe6/work/swebench/runs/gptoss-live-$split-$(date +%Y%m%d-%H%M%S).log
   done
   ```

5. **Stop vLLM Server**
   ```bash
   docker stop vllm-gptoss
   docker rm vllm-gptoss
   ```

6. **Record Metrics**
   - [ ] Extract metrics and save summary

7. **Close Beads Issue**
   ```bash
   bd close <gptoss-issue-id>
   ```

**Success Criteria:**
- Same as Qwen3 section

---

## Phase 5: Results & Reporting

### 5.1 Extract and Aggregate Metrics

**Objective:** Parse evaluation outputs and extract metrics for all model×dataset combinations.

**Tasks:**
- [ ] For each model (4 models):
  - [ ] Parse SWE-bench Multilingual results
    - Total instances: 300
    - Instances solved (passed tests)
    - Pass rate percentage
    - Error breakdown
  - [ ] Parse SWE-bench-Live MultiLang results (8 splits)
    - Per-language totals and pass rates
    - Aggregate totals: 413 instances
    - Error breakdown
  - [ ] Document environmental issues (Go runtime crashes, etc.)
- [ ] Create metrics summary file for each model
  ```bash
  ralph/logs/swebench/metrics-summary-qwen3.json
  ralph/logs/swebench/metrics-summary-deepseek.json
  ralph/logs/swebench/metrics-summary-mixtral.json
  ralph/logs/swebench/metrics-summary-gptoss.json
  ```
- [ ] Create aggregate metrics file
  ```bash
  ralph/logs/swebench/metrics-summary-all.json
  ```

**Success Criteria:**
- Metrics extracted for all 8 model×dataset combinations
- JSON summary files created
- Environmental issues documented

### 5.2 Generate Final Report

**Objective:** Produce markdown report using template structure.

**Tasks:**
- [ ] Update beads issue to `in_progress`
- [ ] Copy template to working document
  ```bash
  cp ralph/plans/SWE_BENCH_MULTILINGUAL_REPORT_TEMPLATE.md \
     ralph/plans/AGENTIC_EVALUATION_REPORT.md
  ```
- [ ] Fill in all sections:
  - [ ] Executive Summary
  - [ ] Overview Table (8 rows: 4 models × 2 datasets)
  - [ ] Per-Model Results (4 sections)
    - SWE-bench Multilingual results
    - SWE-bench-Live MultiLang results with language breakdown
    - Notable errors/patterns
  - [ ] Environment Notes
    - vLLM container tag
    - mini-swe-agent commit hash (from `/tmp/mini-swe-agent-commit.txt`)
    - live-swe-agent commit hash (from `/tmp/live-swe-agent-commit.txt`)
    - Dataset versions (HF shas from spec)
    - Platform details
  - [ ] Known Limitations
    - Go runtime incompatibility details
    - Other environmental issues
    - Affected instance IDs
    - Mitigation attempts
    - Transparency note
- [ ] Review for completeness against spec Section 7.2
- [ ] Proofread and format

**Success Criteria:**
- Report file created at `ralph/plans/AGENTIC_EVALUATION_REPORT.md`
- All required sections completed
- Metrics accurate and traceable to raw outputs
- Report ready for review

### 5.3 Close Report Beads Issue

**Tasks:**
- [ ] Close report beads issue
  ```bash
  bd close <report-issue-id>
  ```
- [ ] Verify all beads issues closed
  ```bash
  bd list --status=open  # Should show no evaluation-related issues
  ```

**Success Criteria:**
- Report beads issue closed
- No open evaluation-related issues remain

---

## Phase 6: Final Cleanup & Commit

### 6.1 Archive Legacy Scripts

**Objective:** Clean up repository by archiving unused direct inference scripts.

**Tasks:**
- [ ] Create archive directory
  ```bash
  mkdir -p scripts/archive/direct-inference
  ```
- [ ] Move legacy scripts (decision based on Phase 1.1 audit)
  ```bash
  # Example if all are unused:
  git mv scripts/swebench_generate_predictions.py scripts/archive/direct-inference/
  git mv scripts/swebench_live_prepare.py scripts/archive/direct-inference/
  git mv scripts/swebench_report_metrics.py scripts/archive/direct-inference/
  # Keep swebench_pull_images.py if still useful
  ```
- [ ] Add README in archive explaining why they were archived
  ```bash
  echo "# Direct Inference Scripts (Archived)" > scripts/archive/direct-inference/README.md
  echo "" >> scripts/archive/direct-inference/README.md
  echo "These scripts were used for the previous direct inference approach." >> scripts/archive/direct-inference/README.md
  echo "Archived on $(date) as part of pivot to agentic-only evaluation." >> scripts/archive/direct-inference/README.md
  ```

**Success Criteria:**
- Legacy scripts archived or decision documented
- Archive README created
- Repository cleaner and focused on agentic approach

### 6.2 Final Git Workflow

**Objective:** Commit all work and push to remote.

**Tasks:**
- [ ] Run git status to see all changes
  ```bash
  git status
  ```
- [ ] Stage all code changes
  ```bash
  git add ralph/plans/EXECUTION_PLAN.md
  git add ralph/plans/AGENTIC_EVALUATION_REPORT.md
  git add ralph/logs/swebench/
  git add scripts/  # If any new scripts or archives
  ```
- [ ] Sync beads changes
  ```bash
  bd sync
  ```
- [ ] Commit code changes with descriptive message
  ```bash
  git commit -m "$(cat <<'EOF'
  feat: Complete agentic SWE-bench multilingual evaluation

  - Implemented agentic evaluation workflow using mini-swe-agent
  - Evaluated 4 models (Qwen3, DeepSeek, Mixtral, GPT-OSS) on 2 datasets
  - Generated comprehensive evaluation report with metrics and insights
  - Archived legacy direct inference scripts
  - Documented execution plan and environment setup

  Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
  EOF
  )"
  ```
- [ ] Sync beads again (in case commit created new beads metadata)
  ```bash
  bd sync
  ```
- [ ] Push to remote
  ```bash
  git push
  ```

**Success Criteria:**
- All changes committed
- Beads synced
- Changes pushed to remote
- Repository up to date

---

## Definition of Done

Work is complete when ALL of the following are true:

- [ ] Old beads issue `dgx-spark-playbooks-a20` closed with reason
- [ ] Existing logs cleared from `ralph/logs/swebench/`
- [ ] mini-swe-agent cloned and installed
- [ ] live-swe-agent cloned
- [ ] Commit hashes recorded for both frameworks
- [ ] **SWE-bench-Live/MultiLang support verified (REQUIRED)**
  - [ ] Determined if native support exists or extension was needed
  - [ ] `--subset live-multilang` option works (natively or via extension)
  - [ ] All 8 language splits validated (c, cpp, go, js, rust, java, ts, cs)
- [ ] **Memory investigation completed (Phase 3.4) (REQUIRED - Added 2026-01-28)** ❌ INCOMPLETE
  - [x] Memory monitoring infrastructure in place (monitor_memory.sh created)
  - [ ] Root cause identified OR safe operating parameters defined (inconclusive - need CONTROLLED TEST DATA)
  - [ ] Controlled testing with monitoring (1, 2, 5 instances) completed and documented (3.4.2)
  - [ ] Comparison with vanilla SWE-bench harness documented (3.4.3)
  - [ ] **UMA buffer cache flushing tested** and effectiveness documented (3.4.4)
  - [ ] Mitigation strategy defined (UMA flushing, memory thresholds, etc.)
  - [x] Investigation report started at [`ralph/logs/swebench/memory-investigation.md`](../logs/swebench/memory-investigation.md) (documents incident only, not controlled tests)
- [x] Configuration files created for all 4 models ✅
- [ ] All 4 models evaluated on SWE-bench Multilingual (300 instances each)
- [ ] All 4 models evaluated on SWE-bench-Live MultiLang (413 instances across 8 splits each)
- [ ] Results saved to structured directories matching spec Section 7.1
- [ ] Metrics extracted for all 8 model×dataset combinations
- [ ] Final report written at `ralph/plans/AGENTIC_EVALUATION_REPORT.md`
- [ ] Report includes all required sections per spec Section 7.2
- [ ] Known limitations documented transparently (including memory issue findings)
- [ ] Legacy scripts audited and archived/removed
- [ ] All beads issues closed
- [ ] All changes committed and pushed to remote repository

**Total Estimated Phases:** 6 (with Phase 3.4 added)
**Total Estimated Tasks:** ~90+ (many are per-model repeats, plus memory investigation)

---

## Notes & Considerations

### Execution Time Expectations

- **mini-swe-agent execution**: No time estimates provided, as evaluation may take significant time per instance
- **vLLM server startup**: Typically 2-5 minutes per model
- **Full workflow**: Expect multiple days for all 4 models × 2 datasets

### Error Handling Strategy

- **Environmental blockers**: Log as beads issue, attempt fix within timeboxed effort, document in plan if unresolved
- **Instance failures**: Continue evaluation, document affected instances in final report's "Known Limitations" section
- **Go runtime crashes**: Known issue with aarch64 emulation, document transparently in report
- **Memory/System Issues**: See Phase 3.4 and [memory investigation report](../logs/swebench/memory-investigation.md) - monitoring must be in place before resuming SWE-bench-Live/MultiLang evaluations

### Config Requirements (Added 2026-01-28)

**⚠️ IMPORTANT:** When creating configs for other models (deepseek, mixtral, gptoss), ensure the submission command is correct:

```yaml
# CORRECT - includes git diff to capture patch:
6. Submit your changes and finish your work by issuing the following command:
   ```bash
   echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached
   ```

# WRONG - do NOT use this (from original live-swe-agent):
6. Submit your changes... `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`. Do not combine it with any other command.
```

Also update the `format_error_template` to use the correct submission command. See Phase 2.4 for full details on this bug.

### Memory Monitoring (Added 2026-01-28)

**⚠️ CRITICAL:** All future evaluation runs MUST include memory monitoring.

**DGX Spark UMA Context:** DGX Spark uses Unified Memory Architecture (UMA) with dynamic GPU/CPU memory sharing. Buffer cache may accumulate between runs. See Phase 3.4.4 for UMA buffer cache flushing procedures.

Before starting any evaluation:
```bash
# Start memory monitor in background
/home/sailorjoe6/work/swebench/scripts/monitor_memory.sh &
MONITOR_PID=$!
echo "Memory monitor PID: $MONITOR_PID"
```

After evaluation completes or before system memory exceeds 90%:
```bash
# Stop monitor
kill $MONITOR_PID
# Review memory log
tail -50 /home/sailorjoe6/work/swebench/runs/memory-monitor-*.log
```

**Memory thresholds:**
- **Warning**: System memory > 80% - consider pausing after current instance, flush UMA buffer cache
- **Critical**: System memory > 90% - stop evaluation, flush UMA buffer cache, investigate before continuing
- **Emergency**: System memory > 95% - immediate stop, risk of crash

**UMA Buffer Cache Flushing** (if memory remains high):
```bash
# Flush cache (requires one-time passwordless sudo setup - see Phase 3.4.4 Prerequisites)
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
```
*See Phase 3.4.4 for passwordless sudo setup and effectiveness testing*

### Parallel vs Sequential

- **Agent generation**: Sequential (--workers 1) due to vLLM server constraints
- **Test evaluation**: Parallel (10 workers) when supported by evaluation framework

### Dataset Support

- `mini-extra swebench` has **documented support** for:
  - `--subset multilingual` for SWE-bench Multilingual ✅
- **SWE-bench-Live/MultiLang support is unclear**:
  - May already work: mini-swe-agent might support it without documenting it
  - May need extension: We'll investigate and extend if needed ⚙️
  - Required features: `--subset live-multilang` and `--split <language>` for 8 splits (c, cpp, go, js, rust, java, ts, cs)
- Investigation and verification is **mandatory** in Phase 2 before model evaluations begin

### Repository Structure

After completion, repository will have:
```
ralph/
  plans/
    SPECIFICATION.md (existing)
    EXECUTION_PLAN.md (this document)
    AGENTIC_EVALUATION_REPORT.md (final report)
  logs/
    swebench/
      swebench-multilingual/
        qwen3/, deepseek/, mixtral/, gptoss/
      swebench-live-multilang/
        qwen3/{c,cpp,go,js,rust,java,ts,cs}/
        deepseek/{c,cpp,go,js,rust,java,ts,cs}/
        mixtral/{c,cpp,go,js,rust,java,ts,cs}/
        gptoss/{c,cpp,go,js,rust,java,ts,cs}/
scripts/
  agentic/ (new wrapper scripts)
  archive/
    direct-inference/ (archived legacy scripts)
```

---

## Appendix: Quick Reference Commands

### Start vLLM for Model
```bash
# Qwen3
docker run -d --name vllm-qwen3-coder --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"

# DeepSeek
docker run -d --name vllm-deepseek-lite --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct" \
    --trust-remote-code --gpu-memory-utilization 0.85 --max-model-len 32768

# Mixtral
docker run -d --name vllm-mixtral-awq --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ" --quantization awq

# GPT-OSS
docker run -d --name vllm-gptoss --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 -p 8000:8000 \
  -v ~/Models/huggingface:/root/.cache/huggingface \
  -v ~/.cache/huggingface/token:/root/.cache/huggingface/token \
  -e HF_HOME=/root/.cache/huggingface \
  nvcr.io/nvidia/vllm:25.12.post1-py3 \
  vllm serve "openai/gpt-oss-120b"
```

### Run Evaluation
```bash
# Activate venv
cd /home/sailorjoe6/work/swebench
source .venv/bin/activate

# SWE-bench Multilingual
mini-extra swebench \
  --model "hosted_vllm/<model-id>" \
  --config configs/<model>-livesweagent.yaml \
  --subset multilingual \
  --split test \
  --workers 1 \
  --output <output-dir>

# SWE-bench-Live MultiLang (loop)
for split in c cpp go js rust java ts cs; do
  mini-extra swebench \
    --model "hosted_vllm/<model-id>" \
    --config configs/<model>-livesweagent.yaml \
    --subset live-multilang \
    --split $split \
    --workers 1 \
    --output <output-dir>/$split
done
```

### Stop vLLM
```bash
docker stop vllm-<container-name>
docker rm vllm-<container-name>
```

### Beads Workflow
```bash
# Check ready work
bd ready

# Update status
bd update <id> --status=in_progress

# Close issue
bd close <id>

# Sync at session end
bd sync
```

---

**End of Execution Plan**
