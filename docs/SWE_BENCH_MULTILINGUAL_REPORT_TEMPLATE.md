# Multilingual SWE-Bench Agentic Evaluation Report

**Date:** YYYY-MM-DD
**Owner:**

---

## Executive Summary

This report presents agentic evaluation results for 4 coding models across 2 multilingual SWE-bench datasets using **mini-swe-agent**. Models were evaluated on their ability to solve repo-level software engineering tasks through iterative exploration and feedback.

**Key Findings**: [Summarize overall performance patterns, which models performed best, any notable observations across datasets]

---

## Overview

| Model | Dataset | Total Tasks | Solved | Pass Rate |
| --- | --- | --- | --- | --- |
| Qwen3-Coder-30B-FP8 | SWE-bench Multilingual | 300 |  |  |
| Qwen3-Coder-30B-FP8 | SWE-bench-Live MultiLang | 413 |  |  |
| DeepSeek-V2-Lite | SWE-bench Multilingual | 300 |  |  |
| DeepSeek-V2-Lite | SWE-bench-Live MultiLang | 413 |  |  |
| Mixtral-8x22B-AWQ | SWE-bench Multilingual | 300 |  |  |
| Mixtral-8x22B-AWQ | SWE-bench-Live MultiLang | 413 |  |  |
| gpt-oss-120b | SWE-bench Multilingual | 300 |  |  |
| gpt-oss-120b | SWE-bench-Live MultiLang | 413 |  |  |

---

## Model Results

### Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8

**SWE-bench Multilingual (300 instances):**
- Total tasks: 300
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml
- Notable errors/patterns:

**SWE-bench-Live MultiLang (413 instances, 8 splits):**
- Total tasks: 413
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml

**Breakdown by language:**
| Language | Tasks | Solved | Pass Rate |
| --- | --- | --- | --- |
| C | 31 |  |  |
| C++ | 17 |  |  |
| Go | 68 |  |  |
| JavaScript | 75 |  |  |
| Rust | 45 |  |  |
| Java | 62 |  |  |
| TypeScript | 87 |  |  |
| C# | 28 |  |  |

**Notable errors/patterns:**

---

### deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct

**SWE-bench Multilingual (300 instances):**
- Total tasks: 300
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml
- Notable errors/patterns:

**SWE-bench-Live MultiLang (413 instances, 8 splits):**
- Total tasks: 413
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml

**Breakdown by language:**
| Language | Tasks | Solved | Pass Rate |
| --- | --- | --- | --- |
| C | 31 |  |  |
| C++ | 17 |  |  |
| Go | 68 |  |  |
| JavaScript | 75 |  |  |
| Rust | 45 |  |  |
| Java | 62 |  |  |
| TypeScript | 87 |  |  |
| C# | 28 |  |  |

**Notable errors/patterns:**

---

### MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ

**SWE-bench Multilingual (300 instances):**
- Total tasks: 300
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml
- Notable errors/patterns:

**SWE-bench-Live MultiLang (413 instances, 8 splits):**
- Total tasks: 413
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml

**Breakdown by language:**
| Language | Tasks | Solved | Pass Rate |
| --- | --- | --- | --- |
| C | 31 |  |  |
| C++ | 17 |  |  |
| Go | 68 |  |  |
| JavaScript | 75 |  |  |
| Rust | 45 |  |  |
| Java | 62 |  |  |
| TypeScript | 87 |  |  |
| C# | 28 |  |  |

**Notable errors/patterns:**

---

### openai/gpt-oss-120b

**SWE-bench Multilingual (300 instances):**
- Total tasks: 300
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml
- Notable errors/patterns:

**SWE-bench-Live MultiLang (413 instances, 8 splits):**
- Total tasks: 413
- Solved:
- Pass rate:
- Configuration: livesweagent.yaml

**Breakdown by language:**
| Language | Tasks | Solved | Pass Rate |
| --- | --- | --- | --- |
| C | 31 |  |  |
| C++ | 17 |  |  |
| Go | 68 |  |  |
| JavaScript | 75 |  |  |
| Rust | 45 |  |  |
| Java | 62 |  |  |
| TypeScript | 87 |  |  |
| C# | 28 |  |  |

**Notable errors/patterns:**

---

## Environment Notes

### Infrastructure
- **Platform**: aarch64 (DGX Spark) with `DOCKER_DEFAULT_PLATFORM=linux/amd64` for emulation
- **amd64 emulation**: Enabled via binfmt/QEMU
- **Docker Hub**: Authenticated with local pull-through cache at `http://127.0.0.1:5000`

### Model Serving
- **vLLM image**: `nvcr.io/nvidia/vllm:25.12.post1-py3`
- **vLLM endpoint**: `http://localhost:8000/v1`
- **HuggingFace cache**: `~/Models/huggingface`

### Agentic Framework
- **mini-swe-agent repository**: `https://github.com/SWE-agent/mini-swe-agent/`
- **mini-swe-agent commit**: [Record after cloning]
- **live-swe-agent repository**: `https://github.com/OpenAutoCoder/live-swe-agent`
- **live-swe-agent commit**: [Record after cloning]
- **Configuration**: `config/livesweagent.yaml` (modified for local vLLM)
- **Agent approach**: Bash-only commands, linear message history, iterative feedback
- **Parallelism**: Sequential agent generation (--workers 1), parallel test evaluation (10 workers)

### Datasets
- **SWE-bench Multilingual**: `SWE-bench/SWE-bench_Multilingual`, split: `test`, HF sha: `2b7aced941b4873e9cad3e76abbae93f481d1beb`
- **SWE-bench-Live MultiLang**: `SWE-bench-Live/MultiLang`, 8 splits (c, cpp, go, js, rust, java, ts, cs), HF sha: `3430730b50bba3ad11b40ca9ba5b224f4034ce1a`

---

## Known Limitations

### Go Runtime Incompatibility (aarch64 + emulation)
- **Affected instances**: [List instance IDs that crashed with Go runtime errors]
- **Root cause**: Go tagged pointer optimization incompatible with QEMU aarch64→amd64 emulation
- **Error signature**: `fatal error: taggedPointerPack`
- **Mitigation attempted**: [GODEBUG flags | QEMU updates | None]
- **Resolution**: [Filtered from results | Ran with workaround | Included with noted failure]
- **Impact on results**: X/413 instances affected (Y%) in SWE-bench-Live MultiLang
- **Note**: These failures are environmental (platform-specific), not model prediction failures

### Other Environmental Issues
[Document any other platform-specific issues discovered during evaluation]

### Evaluation Constraints
[Document any timeouts, resource limits, or other constraints that affected evaluation]
