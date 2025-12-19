#!/usr/bin/env bash
set -euo pipefail

# High-utilization sweeps for multiplier PPG/CPA combinations.
# Reuses /tmp/highutil_mults to avoid shutil SameFileError in run_sweep.py.

SWEEP_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SWEEP_ROOT/../../.." && pwd)"
CONFIG_SRC="$SWEEP_ROOT/configs"
TMP_CFG_DIR="/tmp/highutil_mults"

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
    --out_root "$SWEEP_ROOT" \
    --skip_existing
}

# Remaining sweeps (skip_existing lets you resume safely).
run_platform sky130hd "$SWEEP_ROOT/sweeps/sky130hd_highutil.json"
run_platform asap7    "$SWEEP_ROOT/sweeps/asap7_highutil.json"
# Uncomment to re-run Nangate45 if needed:
# run_platform nangate45 "$SWEEP_ROOT/sweeps/nangate45_highutil.json"

# Summarize best-area runs at the highest successful CORE_UTILIZATION per design.
export SWEEP_ROOT
python3 - <<'PY'
import csv
import json
import os
from pathlib import Path

root = Path(os.environ["SWEEP_ROOT"])
platform_prefix = {
    "nangate45": "mult_ppg_cpa_w4_32_nangate45_highutil",
    "sky130hd": "mult_ppg_cpa_w4_32_sky130hd_highutil",
    "asap7": "mult_ppg_cpa_w4_32_asap7_highutil",
}

best = {}
for metrics_path in root.glob("*/metrics.csv"):
    design = metrics_path.parent.name
    with metrics_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            platform = row["platform"]
            prefix = platform_prefix.get(platform)
            if not prefix or not row["tag"].startswith(prefix):
                continue
            if row["status"] != "ok":
                continue
            try:
                params = json.loads(row["params_json"])
            except json.JSONDecodeError:
                continue
            core_util = float(params.get("CORE_UTILIZATION", 0))
            place_density = params.get("PLACE_DENSITY")
            clock_period = params.get("CLOCK_PERIOD")
            die_area = float(row["die_area"]) if row["die_area"] else None
            key = (design, platform)
            current = best.get(key)
            if current is None:
                best[key] = {
                    "design": design,
                    "platform": platform,
                    "core_util": core_util,
                    "place_density": place_density,
                    "clock_period": clock_period,
                    "critical_path_ns": row.get("critical_path_ns"),
                    "die_area": die_area,
                    "total_power_mw": row.get("total_power_mw"),
                    "result_path": row.get("result_path"),
                    "tag": row.get("tag"),
                }
                continue
            # Prefer highest CORE_UTILIZATION; tie-break on smaller die area when available.
            if core_util > current["core_util"]:
                best[key].update(
                    core_util=core_util,
                    place_density=place_density,
                    clock_period=clock_period,
                    critical_path_ns=row.get("critical_path_ns"),
                    die_area=die_area,
                    total_power_mw=row.get("total_power_mw"),
                    result_path=row.get("result_path"),
                    tag=row.get("tag"),
                )
            elif core_util == current["core_util"]:
                if die_area is not None and (
                    current["die_area"] is None or die_area < current["die_area"]
                ):
                    best[key].update(
                        place_density=place_density,
                        clock_period=clock_period,
                        critical_path_ns=row.get("critical_path_ns"),
                        die_area=die_area,
                        total_power_mw=row.get("total_power_mw"),
                        result_path=row.get("result_path"),
                        tag=row.get("tag"),
                    )

rows = sorted(best.values(), key=lambda r: (r["platform"], r["design"]))
out_path = root / "best_area_highutil.csv"
fieldnames = [
    "design",
    "platform",
    "core_util",
    "place_density",
    "clock_period",
    "critical_path_ns",
    "die_area",
    "total_power_mw",
    "result_path",
    "tag",
]
with out_path.open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"Wrote {len(rows)} rows to {out_path}")
PY
