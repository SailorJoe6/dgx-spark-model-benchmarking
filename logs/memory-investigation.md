# DGX Spark UMA Memory Investigation

Date started: 2026-02-02
Owner: Joe
Status: In progress (tests not started; prior nohup unittest failed because `python` is not on PATH—use `python3`)

## Goal
Run controlled memory tests (1, 2, 5 instances) with monitoring, compare with vanilla evaluation harness, and validate UMA cache flushing effectiveness. Update plan/spec with findings.

## Baseline System State (pre-test)
- Timestamp: 2026-02-02 02:14:00 UTC
- RAM: 119Gi total, 4.8Gi used, 114Gi available
- Swap: 15Gi total, 0B used
- GPU: NVIDIA GB10, driver 580.126.09, util 0%
- Running containers: registry-cache only

## Test Configuration
- Model: deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct (vLLM)
- Dataset: SWE-bench-Live/MultiLang
- Split: c
- mini-swe-agent config: configs/deepseek-livesweagent.yaml
- Command template:
  - Start monitor: `scripts/monitor_memory.sh`
  - Agent run: `mini-extra swebench --config configs/deepseek-livesweagent.yaml --subset "SWE-bench-Live/MultiLang" --split c --slice <slice> --workers 1 --output <output_dir>`
  - Evaluation harness: `python -m evaluation.evaluation --dataset SWE-bench-Live/MultiLang --split c --platform linux --patch_dir <preds.json> --output_dir <eval_dir> --workers 1 --overwrite 0`
- vLLM parameters: `--max-model-len 65536 --gpu-memory-utilization 0.85 --max-num-seqs 1`

## Controlled Tests

### Test A: 1 instance (slice 0:1)
- Monitor log:
- Agent command:
- Agent outcome:
- Peak RAM / swap:
- Notes:

### Test B: 2 instances (slice 0:2)
- Monitor log:
- Agent command:
- Agent outcome:
- Peak RAM / swap:
- Notes:

### Test C: 5 instances (slice 0:5)
- Monitor log:
- Agent command:
- Agent outcome:
- Peak RAM / swap:
- Notes:

## Vanilla Evaluation Harness Comparison
- Command:
- Peak RAM / swap:
- Notes:

## UMA Cache Flush Test
- Command: `echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null`
- Pre-flush available RAM:
- Post-flush available RAM:
- Notes:

## Findings (TBD)
- Memory thresholds:
- Stability limits:
- Recommended mitigations:
