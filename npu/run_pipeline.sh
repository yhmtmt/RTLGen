#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: npu/run_pipeline.sh <arch_config.yml> [--config-out <rtlgen.json>]

Sequential NPU workflow:
  1) validate architecture config
  2) generate RTL (shell stub)
  3) run OpenROAD synthesis (placeholder)
  4) map/schedule (placeholder)
  5) simulate (RTL shell)

This script is a scaffold; wire each step to concrete tools as they are integrated.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

ARCH_CONFIG=""
CONFIG_OUT="npu/rtlgen/examples/from_arch_pipeline.json"
SCHEMA_PATH="npu/arch/schema.yml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-out)
      CONFIG_OUT="$2"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
    *)
      ARCH_CONFIG="$1"
      shift
      ;;
  esac
done

if [[ -z "$ARCH_CONFIG" ]]; then
  usage
  exit 2
fi

if [[ ! -f "$ARCH_CONFIG" ]]; then
  echo "Missing arch config: $ARCH_CONFIG" >&2
  exit 1
fi

echo "[1/5] Validate architecture config"
python3 npu/arch/validate.py "$SCHEMA_PATH" "$ARCH_CONFIG"

echo "[2/5] Generate RTL (shell stub)"
python3 npu/arch/to_rtlgen.py "$ARCH_CONFIG" --out "$CONFIG_OUT"
python3 npu/rtlgen/gen.py --config "$CONFIG_OUT" --out npu/rtlgen/out

echo "[3/5] OpenROAD synthesis (TODO)"
echo "TODO: invoke OpenROAD flow under npu/synth/"

echo "[4/5] Map/schedule (TODO)"
echo "TODO: invoke mapper under npu/mapper/"

echo "[5/5] Simulate (RTL shell)"
make -f npu/sim/rtl/Makefile run CONFIG="$CONFIG_OUT"

echo "Pipeline completed (shell + placeholders)."
