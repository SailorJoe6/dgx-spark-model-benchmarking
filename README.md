# DGX Spark Model Benchmarking

Evaluation infrastructure for benchmarking code LLMs on SWE-bench-Live/MultiLang using the DGX Spark platform.

## Repository

This repository contains all scripts, configs, tests, and documentation for the SWE-bench-Live/MultiLang evaluation project. While it may be checked out locally within other projects, this is the authoritative source.

## Overview

This project evaluates code language models on multilingual SWE-bench datasets using an agentic framework. Models are tested on their ability to solve real-world software engineering tasks across multiple programming languages.

### Benchmarks

We evaluate against **two** multilingual SWE-bench datasets:

| Dataset | Instances | Structure |
|---------|-----------|-----------|
| **[SWE-bench Multilingual](https://www.swebench.com/multilingual.html)** | 300 | Single `test` split |
| **SWE-bench-Live MultiLang** | 413 | 8 language splits |

**SWE-bench Multilingual** breakdown (9 languages): C/C++ (42), Go (42), JS/TS (43), Ruby (44), PHP (43), Java (43), Rust (43)

**SWE-bench-Live MultiLang** breakdown (8 languages): C (31), C++ (17), Go (68), JS (75), Rust (45), Java (62), TS (87), C# (28)

### Frameworks

- **mini-swe-agent** - Lightweight agentic execution framework (forked with streaming support)
- **live-swe-agent** - SWE-bench-tuned agent configs (our configs are based on `livesweagent_swebench.yaml`)
- **SWE-bench / SWE-bench-Live** - Benchmark datasets and evaluation harnesses
- **vLLM** - High-performance LLM serving on DGX Spark

## Directory Structure

```
swebench-eval/
├── configs/           # Model configs (based on live-swe-agent templates)
├── scripts/           # Helper scripts (generation, image pulling, memory monitoring)
├── tests/             # Test suite for configs and scripts
├── docs/              # Documentation
│   ├── SPECIFICATION.md    # Project specification
│   ├── EXECUTION_PLAN.md   # Detailed execution plan
│   └── *.md                # Additional documentation
└── README.md          # This file
```

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [mini-swe-agent fork](https://github.com/SailorJoe6/mini-swe-agent) | Execution framework (with streaming support) |
| [live-swe-agent](https://github.com/SWE-bench-Live/live-swe-agent) | SWE-bench-tuned agent configs (upstream reference) |
| [SWE-bench-Live](https://github.com/SWE-bench-Live/SWE-bench-Live) | Benchmark dataset and evaluation harness |
| [vLLM](https://github.com/vllm-project/vllm) | LLM serving |

## Model Configs

Located in `configs/`, based on live-swe-agent's `livesweagent_swebench.yaml`:

| Config | Model |
|--------|-------|
| `qwen3-livesweagent.yaml` | Qwen3-Coder-30B-A3B-Instruct-FP8 |
| `deepseek-livesweagent.yaml` | DeepSeek-Coder-V2-Lite-Instruct |
| `mixtral-livesweagent.yaml` | Mixtral-8x7B-Instruct-v0.1 |
| `gptoss-livesweagent.yaml` | GPT-OSS-001 |

## Key Features

- **Streaming mode** for vLLM to prevent HTTP timeouts on long generations
- **Pipelined evaluation** - Run test harness in parallel with agent generation
- **Memory-safe operation** - Optimized for DGX Spark's unified memory architecture (119GB)
- **Two-step submission** - Clean patch capture without git warnings polluting output
- **Step limit warnings** - Agent warned at 90% and 100% of step limit to encourage timely submission

## mini-swe-agent Enhancements

Our [fork](https://github.com/SailorJoe6/mini-swe-agent) includes:

### 1. Streaming Mode (`litellm_model.py`)
Prevents HTTP read timeouts on long vLLM generations by streaming responses token-by-token.

### 2. Step Limit Warnings (`agents/default.py`)
Warns agents when approaching step limit:
- **At 90%**: "Running low on steps, wrap up soon"
- **At final step**: "MUST submit NOW"

### 3. Two-Step Submission Process (config change)
Prevents garbage patches by separating `git add` from submission:

```bash
# Step 1: Stage changes (review warnings)
git add -A

# Step 2: Submit clean patch
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git diff --cached
```

This fixes an issue where git warnings (submodules, large files) were corrupting patch output.

## Usage

See [EXECUTION_PLAN.md](docs/EXECUTION_PLAN.md) for detailed instructions.

### Quick Start

```bash
# Activate environment
cd ~/work/swebench && source .venv/bin/activate

# Run evaluation for a split
mini-extra swebench \
  --config configs/qwen3-livesweagent.yaml \
  --subset "SWE-bench-Live/MultiLang" \
  --split c \
  --workers 1 \
  --output ./output/
```

## License

MIT
