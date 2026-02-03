#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat << 'USAGE'
Usage: run_swebench_live_multilang.sh <model_label> <config_path> <output_base_dir>

Arguments:
  model_label       Short label for the model (used in logs/metadata)
  config_path       Path to the mini-swe-agent config YAML
  output_base_dir   Base directory for split outputs (c/cpp/go/js/rust/java/ts/cs)

Environment:
  WORKDIR            Path to work/swebench (default: <repo>/work/swebench)
  WORKERS            mini-extra worker count (default: 1)
  CONTINUE_ON_ERROR  1 to continue on split failure, 0 to stop (default: 1)
  STREAM_USAGE       1 to request streaming usage stats (default: 1)
  DOCKER_DEFAULT_PLATFORM  Must be linux/amd64 (required for SWE-bench containers)
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 3 ]]; then
  usage
  exit 1
fi

MODEL_LABEL="$1"
CONFIG_PATH="$2"
OUTPUT_BASE="$3"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKDIR="${WORKDIR:-${REPO_ROOT}/work/swebench}"
WORKERS="${WORKERS:-1}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-1}"
STREAM_USAGE="${STREAM_USAGE:-1}"
if [[ "${STREAM_USAGE}" -eq 1 ]]; then
  STREAM_USAGE_FLAG="true"
else
  STREAM_USAGE_FLAG="false"
fi

if [[ "${OUTPUT_BASE}" != /* ]]; then
  OUTPUT_BASE="${REPO_ROOT}/${OUTPUT_BASE}"
fi

if [[ ! -d "${WORKDIR}" ]]; then
  echo "ERROR: WORKDIR does not exist: ${WORKDIR}" >&2
  exit 1
fi

if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "ERROR: config path not found: ${CONFIG_PATH}" >&2
  exit 1
fi

if [[ ! -f "${WORKDIR}/.venv/bin/activate" ]]; then
  echo "ERROR: missing venv at ${WORKDIR}/.venv" >&2
  exit 1
fi

require_nohup() {
  if [[ -t 1 ]]; then
    echo "ERROR: This script must be run under nohup (stdout is a TTY)." >&2
    echo "Example:" >&2
    echo "  nohup $0 ${MODEL_LABEL} ${CONFIG_PATH} ${OUTPUT_BASE} > ${OUTPUT_BASE}/nohup.log 2>&1 &" >&2
    exit 1
  fi
}

require_nohup

require_amd64_emulation() {
  local platform="${DOCKER_DEFAULT_PLATFORM:-}"
  if [[ "${platform}" != "linux/amd64" ]]; then
    echo "ERROR: DOCKER_DEFAULT_PLATFORM must be linux/amd64 (current: '${platform:-unset}')." >&2
    echo "Run in this shell:" >&2
    echo "  docker run --privileged --rm tonistiigi/binfmt --install amd64" >&2
    echo "  export DOCKER_DEFAULT_PLATFORM=linux/amd64" >&2
    exit 1
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker not found in PATH; cannot verify amd64 emulation." >&2
    exit 1
  fi

  local arch
  if ! arch="$(docker run --rm --platform=linux/amd64 alpine:3.19 uname -m 2>/dev/null)"; then
    echo "ERROR: amd64 emulation check failed. Re-run binfmt install and try again." >&2
    exit 1
  fi

  if [[ "${arch}" != "x86_64" ]]; then
    echo "ERROR: amd64 emulation check returned '${arch}', expected 'x86_64'." >&2
    exit 1
  fi
}

require_amd64_emulation

mkdir -p "${OUTPUT_BASE}"

SPLITS=(c cpp go js rust java ts cs)
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
SUMMARY_FILE="${OUTPUT_BASE}/run-${MODEL_LABEL}-live-multilang-summary-${TIMESTAMP}.txt"

cd "${WORKDIR}"
# shellcheck disable=SC1091
source "${WORKDIR}/.venv/bin/activate"

{
  echo "start_time: $(date -Is)"
  echo "model_label: ${MODEL_LABEL}"
  echo "config_path: ${CONFIG_PATH}"
  echo "output_base: ${OUTPUT_BASE}"
  echo "workdir: ${WORKDIR}"
  echo "workers: ${WORKERS}"
  echo "continue_on_error: ${CONTINUE_ON_ERROR}"
  echo "stream_usage: ${STREAM_USAGE} (${STREAM_USAGE_FLAG})"
  echo "splits: ${SPLITS[*]}"
  echo
} >> "${SUMMARY_FILE}"

FAILURES=0
for split in "${SPLITS[@]}"; do
  SPLIT_DIR="${OUTPUT_BASE}/${split}"
  mkdir -p "${SPLIT_DIR}"
  LOG_FILE="${SPLIT_DIR}/run-${MODEL_LABEL}-${split}-${TIMESTAMP}.log"

  COMMAND=(
    mini-extra swebench
    --config "${CONFIG_PATH}"
    --subset "SWE-bench-Live/MultiLang"
    --split "${split}"
    --workers "${WORKERS}"
    --output "${SPLIT_DIR}"
  )

  {
    echo "split: ${split}"
    echo "start_time: $(date -Is)"
    printf "command:"
    printf " %q" "${COMMAND[@]}"
    echo
  } >> "${SUMMARY_FILE}"

  set +e
  MSWEA_STREAM_INCLUDE_USAGE="${STREAM_USAGE_FLAG}" "${COMMAND[@]}" 2>&1 | tee "${LOG_FILE}"
  EXIT_CODE=${PIPESTATUS[0]}
  set -e

  echo "exit_code: ${EXIT_CODE}" >> "${SUMMARY_FILE}"
  echo "end_time: $(date -Is)" >> "${SUMMARY_FILE}"
  echo >> "${SUMMARY_FILE}"

  if [[ ${EXIT_CODE} -ne 0 ]]; then
    FAILURES=$((FAILURES + 1))
    if [[ "${CONTINUE_ON_ERROR}" -eq 0 ]]; then
      echo "Stopping after failure in split ${split}." >&2
      break
    fi
  fi

done

if [[ ${FAILURES} -ne 0 ]]; then
  exit 1
fi
