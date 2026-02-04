#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_ROOT="${ROOT_DIR}/work/swebench/logs"

find_active_output_root() {
  local ps_line output_root
  ps_line="$(ps -eo pid=,args= | rg -n "mini-extra swebench" | head -n1 || true)"
  if [[ -z "${ps_line}" ]]; then
    return 1
  fi
  output_root="$(python3 - <<'PY'
import shlex, sys
line = sys.stdin.read().strip()
if not line:
    sys.exit(1)
parts = shlex.split(line)
for i, tok in enumerate(parts):
    if tok == "--output" and i + 1 < len(parts):
        print(parts[i + 1])
        sys.exit(0)
sys.exit(1)
PY
<<<"${ps_line}")"
  if [[ -n "${output_root}" ]]; then
    echo "${output_root}"
    return 0
  fi
  return 1
}

SEARCH_ROOT="${LOG_ROOT}"
if active_root="$(find_active_output_root)"; then
  SEARCH_ROOT="${active_root}"
fi

TAIL_FILE="$(
  find "${SEARCH_ROOT}" -type f -name '*.traj.jsonl' -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr \
    | head -n1 \
    | cut -d' ' -f2-
)"

if [[ -z "${TAIL_FILE}" ]]; then
  if [[ "${SEARCH_ROOT}" != "${LOG_ROOT}" ]]; then
    echo "No .traj.jsonl files found under ${SEARCH_ROOT} (active run output)."
  else
    echo "No .traj.jsonl files found under ${LOG_ROOT}."
  fi
  exit 1
fi

echo "Tailing: ${TAIL_FILE}"
if command -v jq >/dev/null 2>&1; then
  tail -f "${TAIL_FILE}" | jq -C --unbuffered '
    if .role == "tool" then
      {
        ts: (.extra.timestamp // null),
        role: .role,
        output: (.content | tostring)
      }
    else
      {
        ts: (.extra.timestamp // .extra.response.timestamp // null),
        role: .role,
        content: .content,
        tool_calls: (
          .tool_calls // [] | map(
            if (.function? and .function.arguments?) then
              (.function.arguments | (try fromjson catch .) | (if type == "object" and has("command") then .command else . end))
            elif has("arguments") then
              (.arguments | (try fromjson catch .) | (if type == "object" and has("command") then .command else . end))
            else
              .
            end
          )
        )
      }
    end
  '
else
  tail -f "${TAIL_FILE}"
fi
