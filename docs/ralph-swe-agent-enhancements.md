# ralph-swe-agent Enhancements

ralph-swe-agent is a wrapper layer over the vendored [mini-swe-agent](https://github.com/SWE-bench/mini-swe-agent) framework. It adds features needed for SWE-bench evaluation on DGX Spark without modifying the vendored code.

This document covers all enhancements. For evaluation procedures, see [swe-bench-multilingual-evaluation.md](swe-bench-multilingual-evaluation.md).

## Architecture

```
swebench-eval/
  └── work/swebench/ralph-swe-agent/       # Extension layer (submodule)
        ├── src/ralphsweagent/
        │   ├── agents/                     # Custom agents + monkeypatches
        │   ├── models/                     # Model overrides (streaming, guards, tool calls)
        │   ├── config/                     # Seed configs and context window map
        │   └── run/benchmarks/             # Custom SWE-bench runners
        └── vendor/mini-swe-agent/          # Upstream framework (submodule)
```

Three registration functions wire everything together and are called from all entry points:

| Function | Module | Purpose |
|----------|--------|---------|
| `register_model_overrides()` | `ralphsweagent.models` | Redirects model class shortcuts to ralph implementations |
| `register_agent_enhancements()` | `ralphsweagent.agents.enhancements` | Monkeypatches `DefaultAgent` with context window tracking and live trajectory streaming |
| `resolve_agent_class()` | `ralphsweagent.agents` | Resolves agent class names from YAML config |

All three are called automatically by the SWE-bench runners (`swebench.py`, `swebench_single.py`) and the interactive CLI (`mini.py`).

---

## Reasoning Tool-Call Agent

A custom agent that adds a required `reasoning` field to the bash tool call schema, forcing the model to articulate its thought process inside every tool call.

### Why

- With `tool_choice: required`, most LLMs skip the `content` field entirely. The reasoning field ensures thought processes remain in the context window.
- Even without `tool_choice: required`, the extra field prompts models to produce more detailed reasoning, which improves problem-solving performance.

### Configuration

```yaml
agent:
  agent_class: reasoning_tool_call

# Optional: force all turns to use tool calls
model_kwargs:
  tool_choice: required
```

The agent sets `require_reasoning: true` on the model config. Model implementations then use the `BASH_TOOL_WITH_REASONING` schema (which adds a required `reasoning` string parameter to the bash tool) and validate that the field is non-empty on every tool call.

### Tool Schema

Without reasoning (`require_reasoning: false`):
```json
{"name": "bash", "parameters": {"properties": {"command": {"type": "string"}}, "required": ["command"]}}
```

With reasoning (`require_reasoning: true`):
```json
{"name": "bash", "parameters": {"properties": {"reasoning": {"type": "string"}, "command": {"type": "string"}}, "required": ["reasoning", "command"]}}
```

---

## Context Window Tracking

Tracks how much of the model's context window has been consumed after each API call, exposing the information to agent templates.

### How It Works

1. On agent start, the model name is looked up in a local context window map.
2. After each query, `prompt_tokens` from the API response is used to compute `context_left_percent`.
3. Template variables are exposed for use in system/user prompts.

### Template Variables

| Variable | Type | Description |
|----------|------|-------------|
| `context_window_max` | `int \| None` | Maximum context window tokens |
| `context_window_prompt_tokens` | `int \| None` | Prompt tokens used in the last query |
| `context_left_percent` | `int \| None` | Percentage of context remaining (0-100) |

### Context Window Map

A YAML file maps normalized model names to context window sizes. A seed file ships with the package and is copied to `~/.config/mini-swe-agent/model_context_windows.yaml` on first use.

Seeded models include GPT-4/4o, Claude 3.5, Gemini 1.5, Llama 3.1, Qwen 2.5/3, and others.

### Model Name Normalization

Model names are normalized before lookup:

- Provider prefixes stripped (`hosted_vllm/Qwen/Qwen3-Coder` becomes `qwen3-coder`)
- Date suffixes removed (`gpt-4o-2024-08-06` becomes `gpt-4o`)
- Version suffixes removed (`-preview`, `-beta`, `-latest`)
- Quantization suffixes removed (`-fp8`, `-int4`, `-awq`, `-gguf`, etc.)
- Everything lowercased

If no exact match is found, the longest prefix match is used. Unknown models resolved this way are saved to the map for faster future lookups.

---

## LiteLLM Streaming

Streams LLM responses chunk-by-chunk instead of waiting for the full response. This prevents HTTP timeouts during long generations, which is critical for DGX Spark where generation can take minutes.

### Configuration

Environment variables or YAML config:

| Env Var | YAML Field | Default | Description |
|---------|------------|---------|-------------|
| `MSWEA_USE_STREAMING` | `use_streaming` | `false` | Enable response streaming |
| `MSWEA_STREAM_INCLUDE_USAGE` | `stream_include_usage` | `true` | Request usage data in stream chunks |

### Usage Fallback

When streaming is enabled:

1. If the final stream chunk includes valid usage data (non-zero `prompt_tokens` and `completion_tokens`), it is used directly for cost tracking.
2. If usage data is missing or all-zero, a non-streaming retry is performed to get accurate cost data.

This ensures cost tracking works correctly regardless of whether the model provider supports usage reporting in streaming mode.

---

## Stream Guard (Circuit Breaker)

Detects and truncates pathological closing-tag repetition loops where models emit patterns like `</final></final></final>...` indefinitely.

### Configuration

| Env Var | YAML Field | Default | Description |
|---------|------------|---------|-------------|
| `MSWEA_STREAM_GUARD_ENABLED` | `stream_guard_enabled` | `false` | Enable the stream guard |
| `MSWEA_STREAM_GUARD_WINDOW` | `stream_guard_window` | `8192` | Rolling window size in characters |
| `MSWEA_STREAM_GUARD_TAG_THRESHOLD` | `stream_guard_tag_threshold` | `50` | Closing-tag count to trigger truncation |

### How It Works

1. A rolling window of the last `stream_guard_window` characters is checked after each chunk.
2. If the number of closing tags (`</...>`) in the window meets or exceeds `stream_guard_tag_threshold`, the stream is terminated early.
3. Content is truncated to just before the repetition started, preserving valid output.

---

## Live Trajectory Streaming

Streams agent messages to a JSONL file in real time during SWE-bench runs, enabling live monitoring of agent progress.

### File Locations

| Runner | Trajectory JSONL | Final Trajectory |
|--------|-----------------|------------------|
| `mini-extra swebench` | `<output>/<id>/<id>.traj.jsonl` | `<output>/<id>/<id>.traj.json` |
| `mini-extra swebench-single` | Derived from output path (`.json` becomes `.jsonl`) | Output path as specified |

### Lifecycle

1. **Created** — `process_instance` creates the JSONL file and calls `agent.set_live_trajectory_path()`.
2. **Appended** — Every `agent.add_messages()` call appends one JSON line per message with safe serialization.
3. **Deleted** — After the final `.traj.json` is saved successfully, the JSONL file is removed. If the agent crashes, the JSONL remains as a partial record.

### Monitoring

```bash
tail -f output/instance-id/instance-id.traj.jsonl | jq -C '{role, content}'
```

---

## SWE-bench-Live Docker Image Support

The custom runner accepts both `image_name` (standard SWE-bench) and `docker_image` (SWE-bench-Live MultiLang) fields from dataset instances.

| Field | Source Dataset |
|-------|---------------|
| `image_name` | SWE-bench / SWE-bench Multilingual |
| `docker_image` | SWE-bench-Live MultiLang |

When both are present, `image_name` takes priority. If neither is set, the image name is constructed from the `instance_id` using the upstream convention.

---

## Model Configuration Reference

All model settings available in YAML config:

```yaml
model:
  model_name: "hosted_vllm/Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
  model_kwargs: {}                     # Additional API parameters
  cost_tracking: "ignore_errors"       # "default" or "ignore_errors"
  use_streaming: true                  # Enable streaming
  stream_include_usage: true           # Request usage in stream
  stream_guard_enabled: true           # Enable repetition guard
  stream_guard_window: 8192            # Guard window size (chars)
  stream_guard_tag_threshold: 50       # Guard tag count threshold
  tool_choice: null                    # "required" to force tool calls
  require_reasoning: false             # Set automatically by reasoning_tool_call agent
  set_cache_control: null              # "default_end" for Anthropic prompt caching
  format_error_template: "{{ error }}" # Jinja2 template for format errors
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MSWEA_USE_STREAMING` | Enable streaming (bool) |
| `MSWEA_STREAM_INCLUDE_USAGE` | Include usage in streams (bool) |
| `MSWEA_STREAM_GUARD_ENABLED` | Enable repetition guard (bool) |
| `MSWEA_STREAM_GUARD_WINDOW` | Window size (int, chars) |
| `MSWEA_STREAM_GUARD_TAG_THRESHOLD` | Repetition threshold (int, count) |

---

## Agent Configuration Reference

```yaml
agent:
  agent_class: reasoning_tool_call  # "default", "interactive", "reasoning_tool_call", or full module path
  step_limit: 500
  cost_limit: 3.0
  mode: yolo                        # Skip confirmations (swebench-single sets this automatically)
```

---

## Testing

Tests live in `work/swebench/ralph-swe-agent/tests/` and require the project venv:

```bash
source work/swebench/.venv/bin/activate
cd work/swebench/ralph-swe-agent
python -m pytest -q --timeout=90
```

Current test coverage (56 tests):

| Module | Tests |
|--------|-------|
| `test_actions_toolcall` | 16 |
| `test_actions_toolcall_response` | 6 |
| `test_litellm_model` | 12 |
| `test_litellm_response_model` | 2 |
| `test_context_window` | 3 |
| `test_openai_utils` | 4 |
| `test_default` | 3 |
| `test_swebench` | 6 |
| `test_swebench_single` | 4 |
