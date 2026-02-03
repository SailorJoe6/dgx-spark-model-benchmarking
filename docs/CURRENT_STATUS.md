# Current Status - SWE-bench Multilingual Agentic Evaluation

**Last Updated:** 2026-02-03
**Status:** READY (no active runs)

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
- None (no active agentic runs detected)

**Not Started / Pending:**
- ⏳ Phase 4: All model evaluations (Qwen3 → DeepSeek → Mixtral → GPT-OSS)
- ⏳ Phase 5-6: Evaluation reports + cleanup

---

## ✅ What Changed Recently

- Started v2 migration alignment: configs now use native tool calling (`model_class: litellm`) with bash tool prompts.
- Set per-command timeout to 30m (`environment.timeout: 1800`) per spec.
- Pipeline updated to read/write outputs under `work/swebench/logs/...` (no repo-root logs).
- Memory investigation summary retained: `--max-model-len 262144` stable, `--gpu-memory-utilization 0.80` preferred.

---

## ⚠️ Active Work

**Primary beads issues:**
- None open (create new issues before starting evaluations)

---

## 📌 Next Steps (Ordered)

1. Create beads issues for per-model evaluations (Qwen3 → DeepSeek → Mixtral → GPT-OSS) and report.
2. Run Qwen3 multilingual, then live-multilang splits sequentially.
3. Proceed with DeepSeek → Mixtral → GPT-OSS evaluations (same workflow).
4. Run final metrics aggregation + report.
5. Complete cleanup tasks and archive plan/spec if finished.

---

## Notes

- The agentic workflow is the canonical path. Legacy direct-inference scripts remain for reference only.
- See `ralph/plans/EXECUTION_PLAN.md` for the full, detailed execution state.
- Status report (2026-02-03): no running generation/evaluation processes; no preds.json found yet.
