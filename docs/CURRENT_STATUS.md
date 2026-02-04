# Current Status

**Date:** 2026-02-03
**Owner:** Joe

## Summary

Qwen3 agentic multilingual run restarted with updated format error wording. Project is blocked until it completes.

## Active Runs

- **2026-02-04T01:34:18Z** — Qwen3 SWE-bench Multilingual agentic run restarted (experiment: max_completion_tokens=4096).
  - Command:
    `DOCKER_DEFAULT_PLATFORM=linux/amd64 nohup scripts/agentic/run_swebench_multilingual.sh qwen3 /home/sailorjoe6/Code/swebench-eval/work/swebench/configs/qwen3-livesweagent.yaml /home/sailorjoe6/Code/swebench-eval/work/swebench/logs/swebench-multilingual/qwen3 > /home/sailorjoe6/Code/swebench-eval/work/swebench/logs/swebench-multilingual/qwen3/nohup.log 2>&1 &`

## Blocked Work

- `swebench-eval-6ij` — Qwen3 agentic evals (multilingual + live-multilang).

## Next Actions

1. Monitor multilingual run progress and tail latest `*.traj.jsonl` for tool-call issues.
2. After multilingual completes, start live-multilang splits for Qwen3.
3. Unblock the project only after both runs complete or are explicitly stopped.

## Notes

- XML stop sequences remain disabled in configs due to Qwen3 tool-call JSON issues.
- Update this file immediately when a long-running run starts (include timestamp, model, suite, and command).
