# Current Status - SWE-bench Multilingual Agentic Evaluation

**Last Updated:** 2026-02-03
**Status:** BLOCKED (format-error loop investigation)

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
- Investigation: tool calls run real commands initially, then devolve into blank/no-op outputs
  - Issue `swebench-eval-2o4` in progress (blocks Qwen3 evals)
  - Qwen3 run stopped to test default mini-swe-agent prompt
  - Default prompt test hit live-trajectory serialization errors: `SimpleNamespace` not JSON serializable
  - Fixes applied in mini-swe-agent for JSON-safe trajectories + FormatError raw output capture

**Not Started / Pending:**
- ⏳ Phase 4: All model evaluations paused pending `swebench-eval-2o4` resolution
- ⏳ Phase 5-6: Evaluation reports + cleanup

---

## ✅ What Changed Recently

- Started v2 migration alignment: configs now use native tool calling (`model_class: litellm`) with bash tool prompts.
- Set per-command timeout to 30m (`environment.timeout: 1800`) per spec.
- Pipeline updated to read/write outputs under `work/swebench/logs/...` (no repo-root logs).
- Memory investigation summary retained: `--max-model-len 262144` stable, `--gpu-memory-utilization 0.80` preferred.
- mini-swe-agent stacked branch rebase completed; streaming JSONL serialization fix applied and tests pass (submodule now at `029f772`).

---

## ⚠️ Active Work

**Primary beads issues:**
- `swebench-eval-6ij`: Run Qwen3 agentic evals (multilingual + live-multilang)
- `swebench-eval-5xy`: Run DeepSeek agentic evals (multilingual + live-multilang)
- `swebench-eval-4vy`: Run Mixtral agentic evals (multilingual + live-multilang)
- `swebench-eval-u6j`: Run GPT-OSS agentic evals (multilingual + live-multilang)
- `swebench-eval-5yc`: Draft agentic evaluation report

---

## 📌 Next Steps (Ordered)

1. Resolve `swebench-eval-2o4`: re-run default-config test to confirm tool-call formatting; retry Qwen3 run.
2. Start Qwen3 agentic evals (issue `swebench-eval-6ij`).
3. Proceed with DeepSeek → Mixtral → GPT-OSS evaluations (issues `swebench-eval-5xy`, `swebench-eval-4vy`, `swebench-eval-u6j`).
4. Run final metrics aggregation + draft report (issue `swebench-eval-5yc`).
5. Complete cleanup tasks and archive plan/spec if finished.

---

## Notes

- The agentic workflow is the canonical path. Legacy direct-inference scripts remain for reference only.
- See `ralph/plans/EXECUTION_PLAN.md` for the full, detailed execution state.
- Status report (2026-02-03): no running generation/evaluation processes; no preds.json found yet.
