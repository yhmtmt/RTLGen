#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ "$#" -lt 1 ]]; then
  printf 'usage: %s <script> [args...]\n' "$0" >&2
  exit 2
fi

declare -a candidates=()
if [[ -n "${RTLGEN_HF_MATERIALIZER_PYTHON:-}" ]]; then
  candidates+=("${RTLGEN_HF_MATERIALIZER_PYTHON}")
fi
candidates+=("/orfs/tools/AutoTuner/autotuner_env/bin/python3" "python3")

resolve_python() {
  local candidate="$1"
  if [[ "${candidate}" == */* ]]; then
    if [[ -x "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
    return 1
  fi
  command -v "${candidate}"
}

probe_python() {
  local python_bin="$1"
  "${python_bin}" - <<'PY'
import importlib.util
import sys

required = ("torch", "transformers")
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print(
        "missing Hugging Face eval dependencies: " + ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(42)
PY
}

selected_python=""
declare -a attempts=()
for candidate in "${candidates[@]}"; do
  if ! resolved="$(resolve_python "${candidate}")"; then
    attempts+=("${candidate}: not found or not executable")
    printf 'rtlgen hf eval: skipped %s: not found or not executable\n' "${candidate}" >&2
    continue
  fi

  if probe_output="$(probe_python "${resolved}" 2>&1)"; then
    selected_python="${resolved}"
    break
  fi

  attempts+=("${resolved}: ${probe_output}")
  printf 'rtlgen hf eval: skipped %s: %s\n' "${resolved}" "${probe_output}" >&2
done

if [[ -z "${selected_python}" ]]; then
  printf 'rtlgen hf eval: no usable Python found.\n' >&2
  printf 'rtlgen hf eval: set RTLGEN_HF_MATERIALIZER_PYTHON to an interpreter with torch and transformers.\n' >&2
  for attempt in "${attempts[@]}"; do
    printf '  - %s\n' "${attempt}" >&2
  done
  exit 42
fi

version="$("${selected_python}" -c 'import sys; print(sys.version.split()[0])')"
printf 'rtlgen hf eval: using %s (Python %s)\n' "${selected_python}" "${version}" >&2

script="$1"
shift
cd "${repo_root}"
export PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}"
exec "${selected_python}" "${script}" "$@"
