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
- **SWE-bench / SWE-bench-Live** - Benchmark datasets and evaluation harnesses
- **vLLM** - High-performance LLM serving on DGX Spark

## Directory Structure

```
swebench-eval/
├── configs/           # Model configs (maintained locally)
├── scripts/           # Helper scripts (generation, image pulling, memory monitoring)
├── tests/             # Test suite for configs and scripts
├── docs/              # Documentation
│   └── *.md                # Additional documentation
└── README.md          # This file
```

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [mini-swe-agent fork](https://github.com/SailorJoe6/mini-swe-agent) | Execution framework (with streaming support) |
| [SWE-bench-Live](https://github.com/SWE-bench-Live/SWE-bench-Live) | Benchmark dataset and evaluation harness |
| [vLLM](https://github.com/vllm-project/vllm) | LLM serving |

## Model Configs

Located in `configs/`, maintained locally (originally inspired by upstream live-swe-agent settings):

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

## mini-swe-agent Fork Enhancements

Our [fork](https://github.com/SailorJoe6/mini-swe-agent) is stacked on `origin/main` and currently adds:

- **LiteLLM streaming support** with usage fallback and a streaming guard circuit breaker (env vars documented in the fork).
- **Live trajectory streaming** for SWE-bench runs, plus JSON-safe serialization for live JSONL and final trajectories.
- **SWE-bench-Live docker_image support** in the swebench runner (uses dataset `docker_image` field).

## Usage

See `docs/swe-bench-multilingual-evaluation.md` for detailed instructions.

### Quick Start

```bash
# Activate environment
cd work/swebench && source .venv/bin/activate

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
