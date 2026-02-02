# SWE-bench Evaluation Logs - Status

**IMPORTANT: All results in this directory are from INCOMPLETE/INVALID evaluation runs.**

## Why These Results Are Invalid

These evaluation runs were performed **before completing the required setup phases** documented in this repo:

- ❌ Phase 1: Cleanup & Preparation - NOT completed
- ❌ Phase 2.4: Model configurations - INCOMPLETE (only 1 of 4)
- ❌ Phase 3.1: Output directory structure - NOT created
- ❌ Phase 3.2: Evaluation wrapper scripts - NOT created
- ❌ Phase 3.3: Beads issue tracking structure - NOT created
- ❌ **Phase 3.4: Memory investigation - INCOMPLETE (controlled testing not done)**

## Invalid Results Summary

### swebench-multilingual/qwen3/
- Run date: 2026-01-28
- Status: **INCOMPLETE** (17/300 instances, stopped prematurely)
- Issues:
  - No proper directory structure (Phase 3.1 not done)
  - No wrapper scripts used (Phase 3.2 not done)
  - Stopped after only 17 instances
  - Results location unstructured
- Beads issue `dgx-spark-playbooks-o4a` was incorrectly marked as closed

### swebench-live-multilang/qwen3/c/
- Run date: 2026-01-28 02:17-02:21
- Status: **INVALID** (stopped after 2/31 instances, system rebooted)
- Issues:
  - Memory investigation incomplete (Phase 3.4)
  - Config bug caused empty patch submissions
  - System rebooted before completion
  - No memory monitoring active
  - Results cannot be trusted

## What Needs to Happen

The correct sequence is:

1. **Complete Phase 3.4**: Run controlled memory tests with monitoring
   - Test 1, 2, 5 instances sequentially
   - Compare with vanilla SWE-bench harness
   - Identify root cause or define safe operating parameters
   - See beads issue `dgx-spark-playbooks-lom`

2. **Complete remaining setup** (Phase 1-3):
   - Phase 1: Clean up old workflow, audit legacy scripts
   - Phase 2.4: Create 3 remaining model configs (deepseek, mixtral, gptoss)
   - Phase 3.1: Create proper output directory structure
   - Phase 3.2: Create evaluation wrapper scripts
   - Phase 3.3: Create proper beads issue structure

3. **Start Phase 4**: Run all evaluations properly with:
   - Memory monitoring active
   - Proper directory structure
   - Wrapper scripts for reproducibility
   - Full completion of all instances

## Action Required

**According to the cleanup checklist**, these logs should be:
- Backed up (optional): `tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/`
- Cleared: `rm -rf logs/*` (except this README)

Then start fresh with proper Phase 1-4 execution.

---
**Last Updated:** 2026-01-28
**Status:** All results in this directory are INVALID and should not be used for any analysis or reporting.
