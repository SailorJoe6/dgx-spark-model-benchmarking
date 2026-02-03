# Current Status - SWE-bench Multilingual Agentic Evaluation

**Last Updated:** 2026-02-02
**Status:** BLOCKED (Qwen3 run active)

---

## 📋 Quick Status

**Completed:**
- ✅ Phase 2: Frameworks installed (mini-swe-agent + live-swe-agent)
- ✅ Phase 2.4: All model configs created + validated (qwen3, deepseek, mixtral, gptoss)
- ✅ Phase 3.1: Output directories created
- ✅ Phase 3.2: Agentic wrapper scripts created (`scripts/agentic/*.sh`)
- ✅ Phase 3.3: Beads structure created (per-model evaluation issues + report issue)
- ✅ Streaming fix applied to mini-swe-agent (litellm streaming mode)
- ✅ Phase 1 alignment tasks (legacy script audit, timeout policy decision, blocked workflow doc, memory monitor runbook)

**In Progress:**
- 🔄 Qwen3 agentic evaluation running (started 2026-02-02T06:18:44+00:00).

**Not Started / Pending:**
- ⏳ Phase 4: Remaining model evaluations (DeepSeek, Mixtral, GPT-OSS)
- ⏳ Phase 5-6: Evaluation reports + cleanup

---

## ✅ What Changed Recently

- Updated livesweagent configs to `max_completion_tokens: 65536` and `use_streaming: true`, then regenerated model configs.
- Set per-command timeout to 6h (`environment.timeout: 21600`) to avoid unintended command kills during long runs.
- Documented blocked workflow + memory monitor requirements in the runbook.
- Audited legacy scripts and documented their status.
- Memory investigation summary updated: `--max-model-len 262144` stable, `--gpu-memory-utilization 0.80` preferred.
- Qwen3 run restarted cleanly with new vLLM settings.

---

## ⚠️ Active Work

**Primary beads issues:**
- `swebench-eval-a44`: Qwen3 evaluation (in progress)
- `swebench-eval-cxu`: DeepSeek evaluation (open)
- `swebench-eval-tnt`: Mixtral evaluation (open)
- `swebench-eval-g8d`: GPT-OSS evaluation (open)
- `swebench-eval-6n1`: Final report (open)

---

## 📌 Next Steps (Ordered)

1. Let Qwen3 multilingual run complete, then start live-multilang splits sequentially.
2. Proceed with DeepSeek → Mixtral → GPT-OSS evaluations (same workflow).
4. Run final metrics aggregation + report.
5. Complete cleanup tasks and archive plan/spec if finished.

---

## Notes

- The agentic workflow is the canonical path. Legacy direct-inference scripts remain for reference only.
- See `ralph/plans/EXECUTION_PLAN.md` for the full, detailed execution state.
- Qwen3 run: memory monitor started before launch; vLLM + agentic run active.
- vLLM health reports `max_model_len: 262144` and `gpu-memory-utilization: 0.80`.
- Qwen3 run started before output-path fix; its live outputs and `minisweagent.log` are under `work/swebench/logs/swebench-multilingual/qwen3/` (repo-root `logs/` only has `nohup.log` + metadata for this run).
