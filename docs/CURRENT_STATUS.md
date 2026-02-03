# Current Status - SWE-bench Multilingual Agentic Evaluation

**Last Updated:** 2026-01-28
**Status:** Setup phases incomplete, evaluations blocked

---

## 📋 Quick Status

**What's Actually Done:**
- ✅ Phase 2.1-2.3: Frameworks installed (mini-swe-agent, live-swe-agent)
- ✅ Monitoring script created: `/home/sailorjoe6/Code/swebench-eval/work/swebench/scripts/monitor_memory.sh`
- ✅ Incident documented: `logs/memory-investigation.md`

**What's Blocking Everything:**
- ❌ **Phase 3.4: Memory Investigation** - Controlled testing NOT done
  - See beads: `dgx-spark-playbooks-lom`
  - Must complete the controlled memory tests described below

**What Else Needs Doing:**
- ❌ Phase 1: Cleanup & Preparation (all tasks)
- ❌ Phase 2.4: Create 3 remaining configs (deepseek, mixtral, gptoss)
- ❌ Phase 3.1-3.3: Output directories, scripts, beads structure

**Cannot Start Until Setup Complete:**
- ⏸️ Phase 4: All model evaluations (Qwen3, DeepSeek, Mixtral, GPT-OSS)
- ⏸️ Phase 5-6: Reporting and cleanup

---

## 🚨 Critical Findings

### False Completion Claims - CORRECTED

The following were **incorrectly marked as complete** in various documents. They have been corrected:

1. ❌ **Phase 1: Cleanup & Preparation** - NOT started (all checkboxes unchecked)
2. ❌ **Phase 3.4: Memory Investigation** - Script created, incident documented, but **controlled testing NOT done**
3. ❌ **Phase 4.1: Qwen3 evaluations** - Previous runs were INVALID:
   - SWE-bench Multilingual: Only 17/300 instances, stopped prematurely, no proper structure
   - SWE-bench-Live/MultiLang: Only 2/31 instances (C split), system rebooted, empty patches

### Invalid Results

All results in `logs/` are **INVALID** because:
- Evaluations ran before completing required setup phases (1, 2.4, 3.1-3.4)
- No memory monitoring during runs
- Config bugs (empty patch submission issue)
- Incomplete runs (stopped prematurely)
- No proper directory structure or wrapper scripts

See `logs/README.md` for details.

### Beads Issues Cleaned Up

- ✅ Closed `dgx-spark-playbooks-cua` (--yolo flag - unrelated to SWE-bench work)
- ✅ Kept `dgx-spark-playbooks-lom` (memory investigation - accurate description)
- ✅ Kept `dgx-spark-playbooks-zyl` (Qwen3 Live/MultiLang - properly blocked)
- ⚠️ Note: Beads structure doesn't match Phase 3.3 requirements (epic + 4 model issues + report issue)

---

## 📖 Next Steps (In Order)

### Step 1: Complete Phase 3.4 Memory Investigation ⚠️ BLOCKING

**Beads:** `dgx-spark-playbooks-lom`
**Reference:** Controlled test steps listed below

**Required tasks:**

#### 3.4.1: Test memory monitoring script
```bash
cd /home/sailorjoe6/Code/swebench-eval/work/swebench
./scripts/monitor_memory.sh /tmp/test-monitor.log &
MONITOR_PID=$!
sleep 30
kill $MONITOR_PID
cat /tmp/test-monitor.log | tail -10
```

#### 3.4.2: Baseline memory measurements (CRITICAL)
- Start vLLM server for Qwen3
- Record baseline memory (vLLM running, no agent)
- Run mini-swe-agent with monitoring:
  - 1 instance → measure memory
  - 2 instances → measure memory
  - 5 instances → measure memory
- Document: Does memory accumulate between sequential instances?

#### 3.4.3: Compare with vanilla SWE-bench harness
- Run same instances with vanilla harness
- Monitor memory behavior
- Compare: Does vanilla harness release memory properly?

#### 3.4.4: Identify memory leak source
- Check Docker container cleanup
- Check trajectory data accumulation
- Check LiteLLM caching behavior
- Check vLLM KV cache settings

#### 3.4.5: Document findings
- Update `logs/memory-investigation.md` with controlled test results
- Define safe operating parameters OR implement fix

**Success Criteria:**
- Root cause identified OR safe operating parameters defined
- Clear go/no-go decision for Phase 4 evaluations

---

### Step 2: Complete Remaining Setup (Phase 1, 2.4, 3.1-3.3)

Only after Phase 3.4 is complete:

#### Phase 1: Cleanup & Preparation
- Close old beads issue `dgx-spark-playbooks-a20` with reason
- Decide: Clear invalid logs or keep with README warning
- Audit legacy scripts in `scripts/` directory
- Archive or remove as appropriate

#### Phase 2.4: Create remaining configs
Using `qwen3-livesweagent.yaml` as template, create:
- `deepseek-livesweagent.yaml`
- `mixtral-livesweagent.yaml`
- `gptoss-livesweagent.yaml`

**CRITICAL:** Apply the submission command fix to all configs:
```yaml
# CORRECT submission instruction:
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && git add -A && git diff --cached
```

#### Phase 3.1: Create output directories
```bash
mkdir -p logs/swebench-multilingual/{qwen3,deepseek,mixtral,gptoss}
mkdir -p logs/swebench-live-multilang/{qwen3,deepseek,mixtral,gptoss}/{c,cpp,go,js,rust,java,ts,cs}
```

#### Phase 3.2: Create evaluation scripts
- `scripts/agentic/run_swebench_multilingual.sh`
- `scripts/agentic/run_swebench_live_multilang.sh`
- `scripts/agentic/serve_vllm_model.sh`
- `scripts/agentic/stop_vllm_model.sh`

#### Phase 3.3: Create proper beads structure
Per the setup requirements:
- Create beads epic for overall evaluation
- Create 4 beads issues (one per model)
- Add sequential dependencies
- Create final report beads issue

---

### Step 3: Execute Phase 4 Evaluations

Only after Steps 1-2 complete:

Run evaluations in order: Qwen3 → DeepSeek → Mixtral → GPT-OSS

For each model:
- Start memory monitoring FIRST (non-negotiable)
- Use proper wrapper scripts
- Save to structured directories
- Monitor system resources
- Stop vLLM cleanly between models

---

## 📚 Reference Documents

- **Runbook:** `swe-bench-multilingual-evaluation.md` - Step-by-step instructions
- **Report Template:** [SWE_BENCH_MULTILINGUAL_REPORT_TEMPLATE.md](SWE_BENCH_MULTILINGUAL_REPORT_TEMPLATE.md)
- **Memory Investigation:** [logs/memory-investigation.md](../logs/memory-investigation.md) (incident only, not controlled tests)

---

## 🎯 Definition of Done

Work is complete when all setup steps in this document and the runbook are completed.

Currently **MOST ARE UNCHECKED** (~5% complete).

---

**Bottom Line:** We're in the setup phase, not the evaluation phase. The memory investigation must be completed before anything else can proceed.
