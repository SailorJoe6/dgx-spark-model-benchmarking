#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat << 'USAGE'
Usage: pipeline_swebench.sh --suite <multilingual|live-multilang> --model <label>

Options:
  --suite         swebench suite: multilingual or live-multilang
  --model         model label (e.g., qwen3, deepseek, mixtral, gptoss)
  --workers       evaluation worker count (default: env WORKERS or 1)
  --sleep         sleep seconds between loops (default: env SLEEP_SECS or 300)
  --loop          1 to loop until complete, 0 to run once (default: suite-based)
  -h, --help      show this help

Environment:
  WORKDIR         path to work/swebench (default: <repo>/work/swebench)
USAGE
}

SUITE=""
MODEL=""
WORKERS="${WORKERS:-1}"
SLEEP_SECS="${SLEEP_SECS:-300}"
LOOP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --suite)
      SUITE="$2"; shift 2 ;;
    --model)
      MODEL="$2"; shift 2 ;;
    --workers)
      WORKERS="$2"; shift 2 ;;
    --sleep)
      SLEEP_SECS="$2"; shift 2 ;;
    --loop)
      LOOP="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${SUITE}" || -z "${MODEL}" ]]; then
  usage
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKDIR="${WORKDIR:-${REPO_ROOT}/work/swebench}"
LOGS_ROOT="${REPO_ROOT}/logs"

if [[ ! -d "${WORKDIR}" ]]; then
  echo "ERROR: WORKDIR does not exist: ${WORKDIR}" >&2
  exit 1
fi

if [[ ! -f "${WORKDIR}/.venv/bin/activate" ]]; then
  echo "ERROR: missing venv at ${WORKDIR}/.venv" >&2
  exit 1
fi

# Default loop behavior: multilingual loops; live-multilang runs once unless overridden.
if [[ -z "${LOOP}" ]]; then
  if [[ "${SUITE}" == "multilingual" ]]; then
    LOOP=1
  else
    LOOP=0
  fi
fi

convert_preds_to_jsonl() {
  local preds_json="$1"
  local snapshot_jsonl="$2"
  python3 - <<PY
import json
from pathlib import Path
preds_path = Path("${preds_json}")
out_path = Path("${snapshot_jsonl}")
if not preds_path.exists():
    raise SystemExit(2)
with preds_path.open() as f:
    data = json.load(f)
if not isinstance(data, dict):
    raise SystemExit(3)
out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w") as out:
    for v in data.values():
        out.write(json.dumps(v))
        out.write("\n")
print(len(data))
PY
}

run_multilingual_loop() {
  local preds_json="${LOGS_ROOT}/swebench-multilingual/${MODEL}/preds.json"
  local snapshot_jsonl="${WORKDIR}/runs/swebench-multilingual/${MODEL}-preds-partial.jsonl"
  local total=300
  local run_id="${MODEL}-swebench-multilingual"
  local report_dir="${WORKDIR}/runs/swebench-multilingual/reports"

  mkdir -p "${WORKDIR}/runs/swebench-multilingual"

  while true; do
    if [[ ! -f "${preds_json}" ]]; then
      echo "[multilingual] preds.json missing: ${preds_json}"
      if [[ "${LOOP}" -eq 1 ]]; then
        sleep "${SLEEP_SECS}"
        continue
      fi
      exit 1
    fi

    set +e
    count=$(convert_preds_to_jsonl "${preds_json}" "${snapshot_jsonl}")
    rc=$?
    set -e
    if [[ "${rc}" -ne 0 ]]; then
      echo "[multilingual] failed to convert preds.json (rc=${rc})"
      if [[ "${LOOP}" -eq 1 ]]; then
        sleep "${SLEEP_SECS}"
        continue
      fi
      exit 1
    fi

    echo "[multilingual] snapshot: ${snapshot_jsonl} (${count}/${total})"

    # Run evaluation (resumes via run_id)
    source "${WORKDIR}/.venv/bin/activate"
    (cd "${WORKDIR}/SWE-bench" && \
      python -m swebench.harness.run_evaluation \
        --dataset_name SWE-bench/SWE-bench_Multilingual \
        --split test \
        --predictions_path "${snapshot_jsonl}" \
        --max_workers "${WORKERS}" \
        --run_id "${run_id}" \
        --report_dir "${report_dir}")

    if [[ "${count}" -ge "${total}" ]]; then
      echo "[multilingual] predictions complete (${count}/${total}); done."
      break
    fi

    if [[ "${LOOP}" -ne 1 ]]; then
      break
    fi
    sleep "${SLEEP_SECS}"
  done
}

run_live_multilang_loop() {
  local splits=(c cpp go js rust java ts cs)
  local totals=(31 17 68 75 45 62 87 28)
  local any_incomplete=0

  source "${WORKDIR}/.venv/bin/activate"

  while true; do
    any_incomplete=0
    for i in "${!splits[@]}"; do
      local split="${splits[$i]}"
      local total="${totals[$i]}"
      local preds_json="${LOGS_ROOT}/swebench-live-multilang/${MODEL}/${split}/preds.json"
      local out_dir="${WORKDIR}/runs/swebench-live-multilang/eval-results/${MODEL}/${split}"
      local results_json="${out_dir}/results.json"

      if [[ -f "${results_json}" ]]; then
        echo "[live-multilang] ${split}: results.json exists, skipping."
        continue
      fi

      if [[ ! -f "${preds_json}" ]]; then
        echo "[live-multilang] ${split}: preds.json missing."
        any_incomplete=1
        continue
      fi

      count=$(python3 - <<PY
import json
from pathlib import Path
p=Path("${preds_json}")
print(len(json.load(p.open())))
PY
)
      echo "[live-multilang] ${split}: preds ${count}/${total}"

      if [[ "${count}" -lt "${total}" ]]; then
        any_incomplete=1
        continue
      fi

      mkdir -p "${out_dir}"
      (cd "${WORKDIR}/SWE-bench-Live" && \
        python -m evaluation.evaluation \
          --dataset SWE-bench-Live/MultiLang \
          --split "${split}" \
          --platform linux \
          --patch_dir "${preds_json}" \
          --output_dir "${out_dir}" \
          --workers "${WORKERS}" \
          --overwrite 0)
    done

    if [[ "${LOOP}" -ne 1 ]]; then
      break
    fi

    if [[ "${any_incomplete}" -eq 0 ]]; then
      echo "[live-multilang] all splits complete; done."
      break
    fi

    sleep "${SLEEP_SECS}"
  done
}

case "${SUITE}" in
  multilingual)
    run_multilingual_loop
    ;;
  live-multilang)
    run_live_multilang_loop
    ;;
  *)
    echo "ERROR: unknown suite '${SUITE}'" >&2
    exit 1
    ;;
esac
