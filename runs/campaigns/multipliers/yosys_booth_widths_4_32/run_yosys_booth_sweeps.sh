#!/usr/bin/env bash
set -euo pipefail

# Sweep Yosys Booth multipliers (Booth + LowpowerBooth) across platforms.
# Uses /tmp/yosys_booth_cfgs to avoid shutil SameFileError in run_sweep.py.

SWEEP_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SWEEP_ROOT/../../.." && pwd)"
CONFIG_SRC="$SWEEP_ROOT/configs"
DESIGN_ROOT="$REPO_ROOT/runs/designs/multipliers"
TMP_CFG_DIR="/tmp/yosys_booth_cfgs"

mkdir -p "$TMP_CFG_DIR"
cp "$CONFIG_SRC"/*.json "$TMP_CFG_DIR"/

run_platform() {
  local platform="$1"
  local sweep_json="$2"
  echo "===> ${platform} :: $(basename "$sweep_json")"
  python3 "$REPO_ROOT/scripts/run_sweep.py" \
    --configs "$TMP_CFG_DIR"/*.json \
    --platform "$platform" \
    --sweep "$sweep_json" \
    --out_root "$DESIGN_ROOT" \
    --skip_existing
}

# Baseline sweeps (util=10, PD=0.55/0.55/0.55).
run_platform nangate45 "$SWEEP_ROOT/sweeps/nangate45.json"
run_platform sky130hd  "$SWEEP_ROOT/sweeps/sky130hd.json"
run_platform asap7    "$SWEEP_ROOT/sweeps/asap7.json"

# High-util sweeps (dense floorplans).
run_platform nangate45 "$SWEEP_ROOT/sweeps/nangate45_highutil.json"
run_platform sky130hd  "$SWEEP_ROOT/sweeps/sky130hd_highutil.json"
run_platform asap7     "$SWEEP_ROOT/sweeps/asap7_highutil.json"
