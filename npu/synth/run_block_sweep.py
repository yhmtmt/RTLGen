#!/usr/bin/env python3
"""
OpenROAD sweep driver for block-level NPU macros.

Example:
  python npu/synth/run_block_sweep.py \
    --design_dir runs/designs/npu_blocks/dma_stub \
    --platform nangate45 \
    --top dma_stub \
    --sweep npu/synth/block_sweep_example.json
"""

import argparse
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
DEST_BASE = Path("/orfs/flow/designs")
REPORT_BASE = Path("/orfs/flow/reports")
RESULT_BASE = Path("/orfs/flow/results")
SRC_BASE = DEST_BASE / "src"


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_verilog_dir(verilog_dir: Path) -> str:
    hashes = []
    for v in sorted(verilog_dir.glob("*.v")):
        hashes.append(sha1_file(v))
    payload = "".join(hashes)
    return hashlib.sha1(payload.encode()).hexdigest()[:12]


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


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
    content = f"""set clock_port \"clk\"
set clock_period {clock_period}
set input_delay 2.0
set output_delay 2.0

create_clock [get_ports $clock_port] -period $clock_period

set_input_delay $input_delay -clock $clock_port [all_inputs]
set_output_delay $output_delay -clock $clock_port [all_outputs]

set_load -pin_load 0.05 [all_outputs]
"""
    path.write_text(content)


def parse_finish_report(report_path: Path) -> Dict[str, object]:
    metrics: Dict[str, object] = {}
    try:
        lines = report_path.read_text().splitlines()
    except FileNotFoundError:
        return metrics

    for i, line in enumerate(lines):
        if "finish critical path delay" in line and i + 2 < len(lines):
            metrics["critical_path_ns"] = safe_float(lines[i + 2].strip())
            break

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
                    m = re.search(
                        r"DIEAREA\s+\(\s*(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s*\)",
                        line,
                    )
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


def ensure_design_assets(design_name: str, platform: str, top: str, verilog_dir: Path, sdc_template: Path, force: bool):
    dest_platform_dir = DEST_BASE / platform / design_name
    dest_src_dir = SRC_BASE / design_name

    if force or not dest_platform_dir.is_dir():
        dest_src_dir.parent.mkdir(parents=True, exist_ok=True)
        if dest_src_dir.is_dir():
            shutil.rmtree(dest_src_dir)
        shutil.copytree(verilog_dir, dest_src_dir)

        dest_platform_dir.parent.mkdir(parents=True, exist_ok=True)
        if dest_platform_dir.is_dir():
            shutil.rmtree(dest_platform_dir)
        dest_platform_dir.mkdir(parents=True, exist_ok=True)

        verilog_files = [str(p) for p in sorted(dest_src_dir.glob("*.v"))]
        if not verilog_files:
            raise ValueError(f"No .v files found in {verilog_dir}")
        verilog_expr = " ".join(
            f"$(DESIGN_HOME)/src/{design_name}/{Path(v).name}" for v in verilog_files
        )
        config_mk = f"""
export PLATFORM = {platform}
export DESIGN_NAME = {design_name}
export VERILOG_FILES = {verilog_expr}
export SDC_FILE = $(DESIGN_HOME)/{platform}/{design_name}/constraint.sdc
export TOP_MODULE = {top}
export CORE_UTILIZATION = 30
""".lstrip()
        (dest_platform_dir / "config.mk").write_text(config_mk)
        sdc_dst = dest_platform_dir / "constraint.sdc"
        if sdc_template and sdc_template.exists():
            shutil.copy(sdc_template, sdc_dst)
        else:
            write_sdc(10.0, sdc_dst)

    return dest_platform_dir


def append_metrics(metrics_path: Path, row: Dict[str, object]):
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
    needs_header = not metrics_path.exists()
    with metrics_path.open("a") as f:
        if needs_header:
            f.write(",".join(header) + "\n")
        values = [str(row.get(h, "")) for h in header]
        f.write(",".join(values) + "\n")


def run_single(design_dir: Path, design_name: str, platform: str, top: str, verilog_dir: Path,
               sdc_template: Path, sweep_params: Dict[str, object], out_root: Path,
               skip_existing: bool, dry_run: bool, force_copy: bool):
    config_hash = sha1_verilog_dir(verilog_dir)
    run_id = make_run_id(sweep_params)
    tag_prefix = sweep_params.get("TAG") or sweep_params.get("tag_prefix") or "run"
    tag = sweep_params.get("TAG", f"{tag_prefix}_{run_id}")

    circuit_root = out_root / design_name
    work_root = circuit_root / "work"
    run_dir = work_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result_path = run_dir / "result.json"
    if skip_existing and result_path.exists():
        print(f"[INFO] Skipping existing run: {run_dir}")
        return

    if dry_run:
        print(f"[DRY] {design_name} {platform} tag={tag} params={sweep_params}")
        return

    ensure_design_assets(design_name, platform, top, verilog_dir, sdc_template, force_copy)

    clock_period = float(sweep_params.get("CLOCK_PERIOD", 10.0))
    write_sdc(clock_period, DEST_BASE / platform / design_name / "constraint.sdc")

    env = os.environ.copy()
    env.update({k: str(v) for k, v in sweep_params.items()})
    env["TAG"] = tag

    env.setdefault("DISABLE_GUI_SAVE_IMAGES", "1")
    design_config_path = DEST_BASE / platform / design_name / "config.mk"
    sdc_path = DEST_BASE / platform / design_name / "constraint.sdc"
    make_cmd = [
        "make",
        f"DESIGN_CONFIG={design_config_path}",
        f"TAG={tag}",
        f"SDC_FILE={sdc_path}",
    ]
    for k, v in sweep_params.items():
        make_cmd.append(f"{k.upper()}={v}")
    print(f"[INFO] Running OpenROAD flow: {' '.join(make_cmd)}")
    subprocess.run(make_cmd, cwd="/orfs/flow", check=True, env=env)

    report_path = REPORT_BASE / platform / design_name / str(tag) / "6_finish.rpt"
    def_path = RESULT_BASE / platform / design_name / str(tag) / "6_final.def"
    if not report_path.exists():
        report_path = REPORT_BASE / platform / design_name / "base" / "6_finish.rpt"
    if not def_path.exists():
        def_path = RESULT_BASE / platform / design_name / "base" / "6_final.def"

    metrics = parse_finish_report(report_path)
    if platform.lower() == "asap7":
        if metrics.get("critical_path_ns") is not None:
            metrics["critical_path_ns"] = metrics["critical_path_ns"] / 1000.0
        if metrics.get("total_power_mw") is not None:
            metrics["total_power_mw"] = metrics["total_power_mw"] / 1000.0
    metrics["die_area"] = parse_die_area(def_path)
    status = "ok" if metrics.get("critical_path_ns") is not None else "fail"

    payload = {
        "design": design_name,
        "platform": platform,
        "config_hash": config_hash,
        "param_hash": run_id,
        "tag": tag,
        "status": status,
        "critical_path_ns": metrics.get("critical_path_ns"),
        "die_area": metrics.get("die_area"),
        "total_power_mw": metrics.get("total_power_mw"),
        "params_json": json.dumps(sweep_params, sort_keys=True),
        "result_path": str(report_path),
    }
    result_path.write_text(json.dumps(payload, indent=2))

    metrics_path = circuit_root / "metrics.csv"
    append_metrics(metrics_path, payload)


def main():
    ap = argparse.ArgumentParser(description="OpenROAD sweep driver for NPU block macros")
    ap.add_argument("--design_dir", required=True, help="runs/designs/<circuit_type>/<design> path")
    ap.add_argument("--platform", required=True, help="OpenROAD platform name")
    ap.add_argument("--top", required=True, help="Top module name")
    ap.add_argument("--verilog_dir", help="Verilog directory (default: <design_dir>/verilog)")
    ap.add_argument("--sdc", help="Optional SDC template to copy")
    ap.add_argument("--sweep", required=True, help="Sweep JSON")
    ap.add_argument("--out_root", help="Root under runs/designs (default: parent of design_dir)")
    ap.add_argument("--skip_existing", action="store_true", help="Skip existing runs")
    ap.add_argument("--dry_run", action="store_true", help="Print sweep only")
    ap.add_argument("--force_copy", action="store_true", help="Force copy to /orfs/flow")
    args = ap.parse_args()

    design_dir = Path(args.design_dir)
    if not design_dir.is_dir():
        raise FileNotFoundError(design_dir)
    design_name = design_dir.name
    verilog_dir = Path(args.verilog_dir) if args.verilog_dir else design_dir / "verilog"
    if not verilog_dir.is_dir():
        raise FileNotFoundError(verilog_dir)

    out_root = Path(args.out_root) if args.out_root else design_dir.parent
    sweep = load_json(Path(args.sweep))
    grid = sweep.get("flow_params", {})
    combos = cartesian_product(grid)
    tag_prefix = sweep.get("tag_prefix")
    for params in combos:
        if tag_prefix and "tag_prefix" not in params:
            params["tag_prefix"] = tag_prefix
        if "DIE_AREA" in params and "CORE_AREA" in params and "CORE_UTILIZATION" not in params:
            params["CORE_UTILIZATION"] = ""
        run_single(
            design_dir=design_dir,
            design_name=design_name,
            platform=args.platform,
            top=args.top,
            verilog_dir=verilog_dir,
            sdc_template=Path(args.sdc) if args.sdc else None,
            sweep_params=params,
            out_root=out_root,
            skip_existing=args.skip_existing,
            dry_run=args.dry_run,
            force_copy=args.force_copy,
        )


if __name__ == "__main__":
    sys.exit(main())
