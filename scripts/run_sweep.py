#!/usr/bin/env python3
"""
Serial OpenROAD sweep driver (autotuner-free).

Usage example:
    python scripts/run_sweep.py \
        --configs examples/config.json \
        --platform nangate45 \
        --sweep scripts/sweep_example.json \
        --out_root runs/designs/multipliers \
        --dry_run

The sweep file is JSON and must contain a `flow_params` dictionary whose values
are arrays. The Cartesian product of all entries forms the sweep:
{
  "flow_params": {
    "CLOCK_PERIOD": [4.5, 5.0, 6.0],
    "CORE_UTILIZATION": [30, 50],
    "PLACE_DENSITY": [0.55, 0.65]
  },
  "tag_prefix": "sweep1"
}

For each parameter set the script:
1) Ensures RTL and OpenROAD design collateral exist via generate_design.py.
2) Writes a per-run SDC (clock period override) under out_root.
3) Runs OpenROAD via `make` with TAG isolation and env overrides from flow_params.
4) Parses timing/area/power from the resulting reports and writes result.json.
5) Appends a summary row to <design>/metrics.csv for ML ingestion.

Notes:
- Designed to run serially; set --dry_run to print the sweep matrix only.
- Uses only standard library; no Ray/autotuner dependency.
"""

import argparse
import datetime
import hashlib
import itertools
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import shutil
import subprocess
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST_BASE = Path("/orfs/flow/designs")
REPORT_BASE = Path("/orfs/flow/reports")
RESULT_BASE = Path("/orfs/flow/results")
SRC_BASE = DEST_BASE / "src"


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def read_design_names(config_path: Path) -> Tuple[str, str]:
    cfg = load_json(config_path)
    if "multiplier" in cfg:
        module_name = cfg["multiplier"]["module_name"]
    elif "multiplier_yosys" in cfg:
        module_name = cfg["multiplier_yosys"]["module_name"]
    elif "adder" in cfg:
        module_name = cfg["adder"]["module_name"]
    else:
        raise ValueError(f"No multiplier/adder block in {config_path}")
    wrapper = f"{module_name}_wrapper"
    return module_name, wrapper


def ensure_design_assets(config_path: Path, platform: str, force: bool) -> Path:
    """Generate RTL/OpenROAD collateral if missing."""
    _, wrapper = read_design_names(config_path)
    dest_platform_dir = DEST_BASE / platform / wrapper
    if force or not dest_platform_dir.is_dir():
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "generate_design.py"),
            str(config_path),
            platform,
            "--force_gen",
            "True",
        ]
        print(f"[INFO] Generating design collateral: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=REPO_ROOT, check=True)
    return dest_platform_dir


def snapshot_artifacts(config_path: Path, wrapper: str, circuit_root: Path):
    """Copy config and generated Verilog into runs/designs/<circuit_type>/<wrapper>/."""
    circuit_root.mkdir(parents=True, exist_ok=True)
    verilog_out = circuit_root / "verilog"
    verilog_out.mkdir(parents=True, exist_ok=True)

    # Copy config
    shutil.copy(config_path, circuit_root / config_path.name)

    # Copy generated Verilog
    src_dir = SRC_BASE / wrapper
    if src_dir.is_dir():
        for v in src_dir.glob("*.v"):
            shutil.copy(v, verilog_out / v.name)


def cartesian_product(grid: Dict[str, List]) -> List[Dict[str, object]]:
    keys = sorted(grid.keys())
    values = []
    for k in keys:
        v = grid[k]
        if not isinstance(v, list):
            v = [v]
        values.append(v)
    combos = []
    for prod in itertools.product(*values):
        combos.append({k: v for k, v in zip(keys, prod)})
    return combos


def make_run_id(params: Dict[str, object]) -> str:
    payload = json.dumps(params, sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()[:8]


def write_sdc(clock_period: float, path: Path):
    content = f"""set clock_port "clk"
set clock_period {clock_period}
set input_delay 2.0
set output_delay 2.0

create_clock [get_ports $clock_port] -period $clock_period

set_input_delay $input_delay -clock $clock_port [all_inputs]
set_output_delay $output_delay -clock $clock_port [all_outputs]

set_load -pin_load 0.05 [all_outputs]
"""
    path.write_text(content)


def parse_finish_report(report_path: Path, platform: str = "") -> Dict[str, object]:
    metrics: Dict[str, object] = {}
    try:
        lines = report_path.read_text().splitlines()
    except FileNotFoundError:
        return metrics

    # Critical path delay
    for i, line in enumerate(lines):
        if "finish critical path delay" in line and i + 2 < len(lines):
            metrics["critical_path_ns"] = safe_float(lines[i + 2].strip())
            break

    # Power (total)
    for i, line in enumerate(lines):
        if "finish report_power" in line and i + 11 < len(lines):
            parts = lines[i + 11].split()
            if len(parts) >= 5:
                metrics["total_power_mw"] = safe_float(parts[4])
            break

    return metrics


def parse_die_area(def_path: Path) -> float:
    dbu_per_micron = 1.0
    die_area = 0.0

    try:
        with def_path.open() as f:
            for line in f:
                line = line.strip()
                if line.startswith("UNITS DISTANCE MICRONS"):
                    parts = line.replace(";", "").split()
                    if len(parts) >= 4:
                        try:
                            dbu_per_micron = float(parts[3])
                        except ValueError:
                            dbu_per_micron = 1.0
                elif line.startswith("DIEAREA"):
                    # Match DIEAREA ( x1 y1 ) ( x2 y2 )
                    m = re.search(r"DIEAREA\s+\(\s*(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s*\)", line)
                    if m:
                        x1, y1, x2, y2 = map(int, m.groups())
                        width = max(0, x2 - x1)
                        height = max(0, y2 - y1)
                        die_area = float(width * height)
                        break
    except FileNotFoundError:
        return 0.0

    if dbu_per_micron > 0 and die_area > 0:
        return die_area / (dbu_per_micron * dbu_per_micron)
    return 0.0


def safe_float(val):
    try:
        return float(val)
    except Exception:
        return None


def run_single(
    config_path: Path,
    platform: str,
    flow_params: Dict[str, object],
    out_root: Path,
    skip_existing: bool,
    dry_run: bool,
):
    module_name, wrapper = read_design_names(config_path)
    config_hash = sha1_file(config_path)[:12]
    run_id = make_run_id(flow_params)
    tag = flow_params.get("TAG", f"run_{run_id}")

    circuit_root = out_root / wrapper
    work_root = circuit_root / "work"
    run_dir = work_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result_path = run_dir / "result.json"
    if skip_existing and result_path.exists():
        print(f"[INFO] Skipping existing run: {run_dir}")
        return

    # Prepare SDC
    clock_period = None
    for k, v in flow_params.items():
        if k.upper() == "CLOCK_PERIOD":
            clock_period = float(v)
            break
    if clock_period is None:
        clock_period = 10.0
    sdc_path = run_dir / "constraint.sdc"
    write_sdc(clock_period, sdc_path)

    dest_platform_dir = ensure_design_assets(config_path, platform, force=False)
    snapshot_artifacts(config_path, wrapper, circuit_root)
    design_config_path = dest_platform_dir / "config.mk"

    run_record = {
        "design": wrapper,
        "module": module_name,
        "platform": platform,
        "config_path": str(config_path),
        "config_hash": config_hash,
        "param_hash": run_id,
        "tag": tag,
        "flow_params": flow_params,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "reports": {},
        "metrics": {},
        "status": "pending",
    }

    if dry_run:
        run_record["status"] = "dry_run"
        result_path.write_text(json.dumps(run_record, indent=2))
        print(f"[DRY RUN] Would execute make for {wrapper} with params {flow_params}")
        return

    env = os.environ.copy()
    env.setdefault("DISABLE_GUI_SAVE_IMAGES", "1")
    make_cmd = [
        "make",
        f"DESIGN_CONFIG={design_config_path}",
        f"TAG={tag}",
        f"SDC_FILE={sdc_path}",
    ]
    # Pass flow parameters as env overrides (upper-cased keys).
    for k, v in flow_params.items():
        make_cmd.append(f"{k.upper()}={v}")

    print(f"[INFO] Running OpenROAD flow: {' '.join(make_cmd)}")
    try:
        subprocess.run(make_cmd, cwd="/orfs/flow", env=env, check=True)
        run_record["status"] = "ok"
    except subprocess.CalledProcessError as e:
        run_record["status"] = "failed"
        run_record["error"] = str(e)

    # Parse outputs
    finish_rpt = REPORT_BASE / platform / wrapper / str(tag) / "6_finish.rpt"
    def_path = RESULT_BASE / platform / wrapper / str(tag) / "6_final.def"
    # ORFS defaults to FLOW_VARIANT=base; if tag-scoped folders do not exist, fall back.
    if not finish_rpt.exists():
        finish_rpt = REPORT_BASE / platform / wrapper / "base" / "6_finish.rpt"
    if not def_path.exists():
        def_path = RESULT_BASE / platform / wrapper / "base" / "6_final.def"
    run_record["reports"] = {
        "finish": str(finish_rpt),
        "def": str(def_path),
    }
    metrics = parse_finish_report(finish_rpt, platform=platform)
    # ASAP7 finish reports emit picoseconds; convert to nanoseconds for consistency.
    if platform.lower() == "asap7":
        if "critical_path_ns" in metrics and metrics["critical_path_ns"] is not None:
            metrics["critical_path_ns"] = metrics["critical_path_ns"] / 1000.0
    die_area = parse_die_area(def_path)
    if die_area:
        metrics["die_area"] = die_area
    run_record["metrics"] = metrics

    run_record["result_path"] = str(result_path)
    result_path.write_text(json.dumps(run_record, indent=2))
    append_index(circuit_root, run_record)
    print(f"[INFO] Recorded results to {result_path}")


def append_index(circuit_root: Path, record: Dict[str, object]):
    index_path = circuit_root / "metrics.csv"
    header = [
        "design",
        "platform",
        "config_hash",
        "param_hash",
        "tag",
        "status",
        "critical_path_ns",
        "die_area",
        "total_power_mw",
        "params_json",
        "result_path",
    ]
    exists = index_path.exists()
    with index_path.open("a") as f:
        if not exists:
            f.write(",".join(header) + "\n")
        row = [
            record.get("design", ""),
            record.get("platform", ""),
            record.get("config_hash", ""),
            record.get("param_hash", ""),
            record.get("tag", ""),
            record.get("status", ""),
            str(record.get("metrics", {}).get("critical_path_ns", "")),
            str(record.get("metrics", {}).get("die_area", "")),
            str(record.get("metrics", {}).get("total_power_mw", "")),
            json.dumps(record.get("flow_params", {}), sort_keys=True),
            str(Path(record.get("result_path", record.get("param_hash", "")))),
        ]
        f.write(",".join(row) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Autotuner-free OpenROAD sweep runner.")
    parser.add_argument(
        "--configs",
        nargs="+",
        required=True,
        help="List of RTLGen config JSON files to sweep.",
    )
    parser.add_argument(
        "--platform",
        default="nangate45",
        help="PDK/platform name (e.g., nangate45, sky130hd, asap7).",
    )
    parser.add_argument(
        "--sweep",
        required=True,
        help="Path to sweep JSON file (must include flow_params dict).",
    )
    parser.add_argument(
        "--out_root",
        default="runs",
        help="Root directory for per-run outputs and index.csv.",
    )
    parser.add_argument(
        "--skip_existing",
        action="store_true",
        help="Skip runs that already have result.json.",
    )
    parser.add_argument(
        "--force_gen",
        action="store_true",
        help="Regenerate RTL/OpenROAD design collateral before sweeping.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Print sweep matrix and write placeholder result.json without running make.",
    )

    args = parser.parse_args()
    sweep_spec = load_json(Path(args.sweep))
    if "flow_params" not in sweep_spec:
        raise ValueError("Sweep file must contain a 'flow_params' dictionary.")
    flow_grid = sweep_spec["flow_params"]
    tag_prefix = sweep_spec.get("tag_prefix", "sweep")
    out_root = (REPO_ROOT / args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    combos = cartesian_product(flow_grid)
    print(f"[INFO] Loaded {len(combos)} parameter sets from {args.sweep}")

    for cfg in args.configs:
        config_path = Path(cfg).resolve()
        if not config_path.is_file():
            raise FileNotFoundError(f"Config not found: {config_path}")
        if args.force_gen:
            ensure_design_assets(config_path, args.platform, force=True)

        for params in combos:
            params = {k.upper(): v for k, v in params.items()}
            params.setdefault("TAG", f"{tag_prefix}_{make_run_id(params)}")
            run_single(
                config_path=config_path,
                platform=args.platform,
                flow_params=params,
                out_root=out_root,
                skip_existing=args.skip_existing,
                dry_run=args.dry_run,
            )


if __name__ == "__main__":
    main()
