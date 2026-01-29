# DGX Spark Model Benchmarking

Evaluation infrastructure for benchmarking code LLMs on SWE-bench-Live/MultiLang using the DGX Spark platform.

## Overview

This project provides tools for running agentic evaluations of code language models using:
- **mini-swe-agent** - Agentic framework for code tasks
- **SWE-bench-Live/MultiLang** - Multilingual benchmark (C, C++, Go, JS, Rust, Java, TypeScript, C#)
- **vLLM** - High-performance LLM serving

## Directory Structure

```
swebench-eval/
├── configs/           # Model configuration files for mini-swe-agent
├── scripts/           # Helper scripts (generation, image pulling, memory monitoring)
├── tests/             # Test suite for configs and scripts
├── docs/              # Documentation
│   ├── SPECIFICATION.md    # (symlink) Project specification
│   ├── EXECUTION_PLAN.md   # (symlink) Detailed execution plan
│   └── *.md                # Additional documentation
└── README.md          # This file
```

## Related Repositories

- [mini-swe-agent fork](https://github.com/SailorJoe6/mini-swe-agent) - Fork with streaming support
- [SWE-bench-Live](https://github.com/SWE-bench-Live) - Benchmark dataset
- [vLLM](https://github.com/vllm-project/vllm) - LLM serving

## Model Configs

Located in `configs/`:
- `qwen3-livesweagent.yaml` - Qwen3-Coder-30B-A3B-Instruct-FP8
- `deepseek-livesweagent.yaml` - DeepSeek-Coder-V2-Lite-Instruct
- `mixtral-livesweagent.yaml` - Mixtral-8x7B-Instruct-v0.1
- `gptoss-livesweagent.yaml` - GPT-OSS-001

## Key Features

- **Streaming mode** for vLLM to prevent HTTP timeouts on long generations
- **Pipelined evaluation** - Run test harness in parallel with agent generation
- **Memory-safe operation** - Optimized for DGX Spark's unified memory architecture

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
