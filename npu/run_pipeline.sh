#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: npu/run_pipeline.sh <arch_config.yml>

Sequential NPU workflow:
  1) validate architecture config
  2) generate RTL (placeholder)
  3) run OpenROAD synthesis (placeholder)
  4) map/schedule (placeholder)
  5) simulate (placeholder)

This script is a scaffold; wire each step to concrete tools as they are integrated.
EOF
}

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

ARCH_CONFIG="$1"
SCHEMA_PATH="npu/arch/schema.yml"

if [[ ! -f "$ARCH_CONFIG" ]]; then
  echo "Missing arch config: $ARCH_CONFIG" >&2
  exit 1
fi

echo "[1/5] Validate architecture config"
python3 npu/arch/validate.py "$SCHEMA_PATH" "$ARCH_CONFIG"

echo "[2/5] Generate RTL (TODO)"
echo "TODO: invoke NPU RTL generator under npu/rtlgen/"

echo "[3/5] OpenROAD synthesis (TODO)"
echo "TODO: invoke OpenROAD flow under npu/synth/"

echo "[4/5] Map/schedule (TODO)"
echo "TODO: invoke mapper under npu/mapper/"

echo "[5/5] Simulate (TODO)"
echo "TODO: invoke simulator under npu/sim/"

echo "Pipeline completed (placeholders)."
