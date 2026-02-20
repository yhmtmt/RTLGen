#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: npu/run_pipeline.sh <arch_config.yml> [--config-out <rtlgen.json>] [--sram-id <id>] [--golden]
       [--sram-pre-mode <auto|memgen_only|cacti_only>]
       [--sram-memgen-cmd <command-template>]
       [--sram-memgen-metrics <metrics-template>]
       [--sram-cacti-bin <path>]

Sequential NPU workflow:
  1) validate architecture config
  2) generate RTL (shell stub)
  3) pre-synthesis SRAM stage (macro generation when available, else CACTI fallback)
  4) run OpenROAD synthesis (placeholder)
  5) map/schedule (placeholder)
  6) simulate (RTL shell)
  7) golden mapper + RTL + perf sim (optional)

This script is a scaffold; wire each step to concrete tools as they are integrated.
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

ARCH_CONFIG=""
CONFIG_OUT="npu/rtlgen/examples/from_arch_pipeline.json"
SRAM_ID=""
SCHEMA_PATH=""
RUN_GOLDEN=0
SRAM_PRE_MODE="auto"
SRAM_MEMGEN_CMD=""
SRAM_MEMGEN_METRICS=""
SRAM_CACTI_BIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-out)
      CONFIG_OUT="$2"
      shift 2
      ;;
    --sram-id)
      SRAM_ID="$2"
      shift 2
      ;;
    --sram-pre-mode)
      SRAM_PRE_MODE="$2"
      shift 2
      ;;
    --sram-memgen-cmd)
      SRAM_MEMGEN_CMD="$2"
      shift 2
      ;;
    --sram-memgen-metrics)
      SRAM_MEMGEN_METRICS="$2"
      shift 2
      ;;
    --sram-cacti-bin)
      SRAM_CACTI_BIN="$2"
      shift 2
      ;;
    --golden)
      RUN_GOLDEN=1
      shift
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

if [[ -z "$SRAM_ID" ]]; then
  SRAM_ID="$(basename "$ARCH_CONFIG")"
  SRAM_ID="${SRAM_ID%.*}"
fi

SCHEMA_PATH="$(python3 - "$ARCH_CONFIG" <<'PY'
import sys
from pathlib import Path
import yaml

cfg = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8")) or {}
ver = str(cfg.get("schema_version", "")).strip()
if ver == "0.2-draft":
    print("npu/arch/schema_v0_2_draft.yml")
else:
    print("npu/arch/schema.yml")
PY
)"

if [[ "$SRAM_PRE_MODE" != "auto" && "$SRAM_PRE_MODE" != "memgen_only" && "$SRAM_PRE_MODE" != "cacti_only" ]]; then
  echo "Invalid --sram-pre-mode: $SRAM_PRE_MODE" >&2
  exit 2
fi

echo "[1/6] Validate architecture config"
python3 npu/arch/validate.py "$SCHEMA_PATH" "$ARCH_CONFIG"

echo "[2/6] Generate RTL (shell stub)"
python3 npu/arch/to_rtlgen.py "$ARCH_CONFIG" --out "$CONFIG_OUT"
python3 npu/rtlgen/gen.py --config "$CONFIG_OUT" --out npu/rtlgen/out

echo "[3/6] Pre-synthesis SRAM stage"
SRAM_PRE_CMD=(
  python3 npu/synth/pre_synth_memory.py "$ARCH_CONFIG"
  --id "$SRAM_ID"
  --mode "$SRAM_PRE_MODE"
)
if [[ -n "$SRAM_MEMGEN_CMD" ]]; then
  SRAM_PRE_CMD+=(--memgen-cmd "$SRAM_MEMGEN_CMD")
fi
if [[ -n "$SRAM_MEMGEN_METRICS" ]]; then
  SRAM_PRE_CMD+=(--memgen-metrics "$SRAM_MEMGEN_METRICS")
fi
if [[ -n "$SRAM_CACTI_BIN" ]]; then
  SRAM_PRE_CMD+=(--cacti-bin "$SRAM_CACTI_BIN")
fi
"${SRAM_PRE_CMD[@]}"

echo "[4/6] OpenROAD synthesis (TODO)"
echo "TODO: invoke OpenROAD flow under npu/synth/"

echo "[5/6] Map/schedule (TODO)"
echo "TODO: invoke mapper under npu/mapper/"

echo "[6/6] Simulate (RTL shell)"
make -f npu/sim/rtl/Makefile run CONFIG="$CONFIG_OUT"

if [[ "$RUN_GOLDEN" -eq 1 ]]; then
  echo "[7/7] Golden mapper + RTL + perf sim"
  npu/sim/run_golden.sh
fi

echo "Pipeline completed (shell + placeholders)."
