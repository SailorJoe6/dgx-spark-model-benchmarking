# Current Status

**Date:** 2026-02-03
**Owner:** Joe

## Summary

Qwen3 agentic multilingual run stopped and outputs cleared due to empty patches. Ready to restart with patch.txt submission flow.

## Active Runs

- None.

## Blocked Work

- `swebench-eval-6ij` — Qwen3 agentic evals (multilingual + live-multilang).

## Next Actions

1. Restart Qwen3 multilingual run with the patch.txt submission flow.
2. Start pipelined evaluation after predictions resume.

## Notes

- XML stop sequences remain disabled in configs due to Qwen3 tool-call JSON issues.
- **2026-02-04:** Missing tool-call FormatError loop issue is resolved (no longer an active risk).
- Update this file immediately when a long-running run starts (include timestamp, model, suite, and command).
