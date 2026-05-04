#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
materializer="${repo_root}/npu/eval/materialize_hf_decoder_contract.py"

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

required = ("torch", "transformers", "onnx")
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    print(
        "missing Hugging Face materializer dependencies: " + ", ".join(missing),
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
    printf 'rtlgen hf materializer: skipped %s: not found or not executable\n' "${candidate}" >&2
    continue
  fi

  if probe_output="$(probe_python "${resolved}" 2>&1)"; then
    selected_python="${resolved}"
    break
  fi

  attempts+=("${resolved}: ${probe_output}")
  printf 'rtlgen hf materializer: skipped %s: %s\n' "${resolved}" "${probe_output}" >&2
done

if [[ -z "${selected_python}" ]]; then
  printf 'rtlgen hf materializer: no usable Python found for Hugging Face export.\n' >&2
  printf 'rtlgen hf materializer: set RTLGEN_HF_MATERIALIZER_PYTHON to an interpreter with torch, transformers, and onnx.\n' >&2
  for attempt in "${attempts[@]}"; do
    printf '  - %s\n' "${attempt}" >&2
  done
  exit 42
fi

version="$("${selected_python}" -c 'import sys; print(sys.version.split()[0])')"
printf 'rtlgen hf materializer: using %s (Python %s)\n' "${selected_python}" "${version}" >&2

cd "${repo_root}"
exec "${selected_python}" "${materializer}" "$@"
