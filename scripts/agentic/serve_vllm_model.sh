#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat << 'USAGE'
Usage: serve_vllm_model.sh <model_key>

Model keys:
  qwen3      Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8
  deepseek   deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct
  mixtral    MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ
  gptoss     openai/gpt-oss-120b

Environment overrides:
  VLLM_IMAGE             (default: nvcr.io/nvidia/vllm:25.12.post1-py3)
  VLLM_PORT              (default: 8000)
  VLLM_MAX_MODEL_LEN     (default: 262144)
  VLLM_GPU_MEMORY_UTIL   (default: 0.80)
  VLLM_MAX_NUM_SEQS      (default: 1)
  VLLM_KV_CACHE_DTYPE    (optional, e.g. fp8_e4m3)
  VLLM_EXTRA_ARGS        (optional additional vllm args)
  VLLM_HEALTH_URL        (default: http://localhost:8000/v1/models)
  VLLM_HEALTH_TIMEOUT    (default: 300)
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

MODEL_KEY="$1"

VLLM_IMAGE="${VLLM_IMAGE:-nvcr.io/nvidia/vllm:25.12.post1-py3}"
VLLM_PORT="${VLLM_PORT:-8000}"
VLLM_MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-262144}"
VLLM_GPU_MEMORY_UTIL="${VLLM_GPU_MEMORY_UTIL:-0.80}"
VLLM_MAX_NUM_SEQS="${VLLM_MAX_NUM_SEQS:-1}"
VLLM_KV_CACHE_DTYPE="${VLLM_KV_CACHE_DTYPE:-}"
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"
VLLM_HEALTH_URL="${VLLM_HEALTH_URL:-http://localhost:${VLLM_PORT}/v1/models}"
VLLM_HEALTH_TIMEOUT="${VLLM_HEALTH_TIMEOUT:-300}"

MODEL_NAME=""
CONTAINER_NAME=""
MODEL_ARGS=()

case "${MODEL_KEY}" in
  qwen3)
    MODEL_NAME="Qwen/Qwen3-Coder-30B-A3B-Instruct-FP8"
    CONTAINER_NAME="vllm-qwen3-coder"
    ;;
  deepseek)
    MODEL_NAME="deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"
    CONTAINER_NAME="vllm-deepseek-lite"
    MODEL_ARGS+=(--trust-remote-code)
    ;;
  mixtral)
    MODEL_NAME="MaziyarPanahi/Mixtral-8x22B-Instruct-v0.1-AWQ"
    CONTAINER_NAME="vllm-mixtral-awq"
    MODEL_ARGS+=(--quantization awq)
    ;;
  gptoss)
    MODEL_NAME="openai/gpt-oss-120b"
    CONTAINER_NAME="vllm-gptoss"
    ;;
  *)
    echo "ERROR: unknown model key: ${MODEL_KEY}" >&2
    usage
    exit 1
    ;;
 esac

if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "ERROR: container already exists: ${CONTAINER_NAME}" >&2
  exit 1
fi

if [[ -n "${VLLM_KV_CACHE_DTYPE}" ]]; then
  MODEL_ARGS+=(--kv-cache-dtype "${VLLM_KV_CACHE_DTYPE}")
fi

if [[ -n "${VLLM_EXTRA_ARGS}" ]]; then
  # shellcheck disable=SC2206
  MODEL_ARGS+=(${VLLM_EXTRA_ARGS})
fi

DOCKER_RUN=(
  docker run -d --name "${CONTAINER_NAME}" --gpus all --ipc=host
  --ulimit memlock=-1 --ulimit stack=67108864
  -p "${VLLM_PORT}:8000"
  -v "${HOME}/Models/huggingface:/root/.cache/huggingface"
  -v "${HOME}/.cache/huggingface/token:/root/.cache/huggingface/token"
  -e HF_HOME=/root/.cache/huggingface
  "${VLLM_IMAGE}"
  vllm serve "${MODEL_NAME}"
  --max-model-len "${VLLM_MAX_MODEL_LEN}"
  --gpu-memory-utilization "${VLLM_GPU_MEMORY_UTIL}"
  --max-num-seqs "${VLLM_MAX_NUM_SEQS}"
  "${MODEL_ARGS[@]}"
)

printf "Starting container: %s\n" "${CONTAINER_NAME}"
"${DOCKER_RUN[@]}" >/dev/null

START_TIME=$(date +%s)
while true; do
  if curl -sf "${VLLM_HEALTH_URL}" >/dev/null; then
    echo "vLLM is healthy at ${VLLM_HEALTH_URL}"
    break
  fi
  NOW=$(date +%s)
  if (( NOW - START_TIME > VLLM_HEALTH_TIMEOUT )); then
    echo "ERROR: vLLM health check timed out after ${VLLM_HEALTH_TIMEOUT}s" >&2
    exit 1
  fi
  sleep 5
 done
