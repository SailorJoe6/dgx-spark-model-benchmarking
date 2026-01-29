# vLLM Model Compatibility on DGX Spark

This document summarizes the vLLM model compatibility work for DGX Spark and points to the reproducible commands and results.

## Scope

- Single DGX Spark testing only
- vLLM container: `nvcr.io/nvidia/vllm:25.12.post1-py3`
- OpenAI-compatible API tests via `/v1/chat/completions`

## Summary

| Model | Status | Quantization | Notes |
|-------|--------|--------------|-------|
| GPT-OSS-120B | ✅ Success | MXFP4 | Works with default settings. |
| Qwen3-Coder-30B-A3B-Instruct | ✅ Success | FP8 | Official FP8 variant works. |
| Qwen2.5-72B-Instruct | ✅ Success | FP8 | Compressed-tensors FP8 variant works. |
| Mixtral 8x22B-Instruct | ✅ Success | AWQ 4-bit | AWQ variant works with `--quantization awq`. |
| DeepSeek-Coder-V2-Lite-Instruct | ✅ Success | BF16 | Requires reduced max length to fit comfortably. |
| DBRX-Instruct | ❌ Failed | FP8 (attempted) | OOM even with reduced context; no 4-bit instruct variant available. |
| DeepSeek-Coder-V2-Instruct | ❌ Not feasible | None available | No compatible FP8/AWQ/GPTQ/NVFP4 variants found; full precision far exceeds memory limits. |

## Where to find details

- Full test log and run commands: `ralph/plans/VLLM_TEST_RESULTS.md`
- Execution plan and decisions: `ralph/plans/EXECUTION_PLAN.md`
- Playbook support matrix (published): `nvidia/vllm/README.md`

## Notes for future work

- If a 4-bit or FP8 DeepSeek-Coder-V2-Instruct checkpoint appears, re-run Phase 7 and update the support matrix.
