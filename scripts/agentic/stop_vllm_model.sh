#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat << 'USAGE'
Usage: stop_vllm_model.sh <model_key|container_name>

Model keys:
  qwen3      vllm-qwen3-coder
  deepseek   vllm-deepseek-lite
  mixtral    vllm-mixtral-awq
  gptoss     vllm-gptoss

You may also pass a container name directly.
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

INPUT="$1"
CONTAINER_NAME=""

case "${INPUT}" in
  qwen3)
    CONTAINER_NAME="vllm-qwen3-coder"
    ;;
  deepseek)
    CONTAINER_NAME="vllm-deepseek-lite"
    ;;
  mixtral)
    CONTAINER_NAME="vllm-mixtral-awq"
    ;;
  gptoss)
    CONTAINER_NAME="vllm-gptoss"
    ;;
  *)
    CONTAINER_NAME="${INPUT}"
    ;;
 esac

if ! docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  echo "Container not found: ${CONTAINER_NAME}" >&2
  exit 1
fi

printf "Stopping container: %s\n" "${CONTAINER_NAME}"
docker stop "${CONTAINER_NAME}" >/dev/null
printf "Removing container: %s\n" "${CONTAINER_NAME}"
docker rm "${CONTAINER_NAME}" >/dev/null
