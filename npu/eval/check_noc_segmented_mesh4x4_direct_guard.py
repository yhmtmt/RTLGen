#!/usr/bin/env python3
"""Guard exact source identity and pin-perimeter feasibility of the direct mesh top."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = REPO_ROOT / "npu" / "sim" / "rtl"
SOURCE_NAMES = (
    "noc_ready_valid_fifo.sv",
    "noc_segmented_mesh_router.sv",
    "noc_segmented_mesh4x4.sv",
    "noc_segmented_mesh4x4_functional.sv",
)
EXPECTED_PROFILE = {
    "nodes": 16,
    "ports_per_router": 5,
    "data_bits": 256,
    "virtual_channels": 4,
    "fifo_depth": 4,
    "debug_counters": False,
    "top_level_pin_count": 8962,
    "pin_pitch_bound_um": 1.12,
    "die_side_um": 3200,
}


def minimum_square_side_um(pin_count: int, pin_pitch_bound_um: float) -> float:
    return pin_count * pin_pitch_bound_um / 4.0


def check(config_path: Path, verilog_dir: Path) -> dict[str, float]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("top_name") != "noc_segmented_mesh4x4_functional":
        raise ValueError("physical and replay top must be noc_segmented_mesh4x4_functional")
    profile = config.get("segmented_mesh4x4_direct")
    if profile != EXPECTED_PROFILE:
        raise ValueError(f"direct-mesh profile mismatch: expected {EXPECTED_PROFILE}, got {profile}")

    staged_paths: list[Path] = []
    for name in SOURCE_NAMES:
        staged = verilog_dir / name
        canonical = CANONICAL_DIR / name
        if not staged.is_file() or staged.read_bytes() != canonical.read_bytes():
            raise ValueError(f"staged mesh source differs from canonical RTL source: {name}")
        staged_paths.append(staged)

    mesh_source = (verilog_dir / "noc_segmented_mesh4x4.sv").read_text(encoding="utf-8")
    if mesh_source.count("noc_segmented_mesh_router #(") != 1:
        raise ValueError("direct mesh source must contain one generated sixteen-node router template")
    for required in (
        "for (node_g = 0; node_g < NODES; node_g = node_g + 1)",
        "endpoint_in_data",
        "endpoint_out_data",
        "router_route_flit_count",
    ):
        if required not in mesh_source:
            raise ValueError(f"direct mesh source is missing required structure: {required}")

    specialization = (verilog_dir / "noc_segmented_mesh4x4_functional.sv").read_text(
        encoding="utf-8"
    )
    if "always" in specialization or specialization.count(") u_mesh (") != 1:
        raise ValueError("functional mesh specialization must be logic-free and instantiate one mesh")
    if specialization.count(".ENABLE_DEBUG_COUNTERS(0)") != 1:
        raise ValueError("functional mesh specialization must disable debug-counter state")
    for debug_port in (
        "router_accepted_flit_count",
        "router_forwarded_flit_count",
        "router_route_flit_count",
    ):
        if f".{debug_port}()" not in specialization:
            raise ValueError(f"functional mesh specialization must omit debug output {debug_port}")

    required_perimeter_um = (
        EXPECTED_PROFILE["top_level_pin_count"] * EXPECTED_PROFILE["pin_pitch_bound_um"]
    )
    available_perimeter_um = 4.0 * EXPECTED_PROFILE["die_side_um"]
    if available_perimeter_um < required_perimeter_um:
        raise ValueError("direct mesh die perimeter is below the pin-placement lower bound")
    minimum_side_um = minimum_square_side_um(
        EXPECTED_PROFILE["top_level_pin_count"], EXPECTED_PROFILE["pin_pitch_bound_um"]
    )
    if not math.isclose(minimum_side_um, 2509.36, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("direct mesh pin-perimeter calculation changed unexpectedly")

    yosys = shutil.which("yosys") or "/oss-cad-suite/bin/yosys"
    hierarchy_check = subprocess.run(
        [
            yosys,
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in staged_paths)
            + "; hierarchy -check -top noc_segmented_mesh4x4_functional; "
            + "select -list t:*noc_segmented_mesh_router*",
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    router_nodes = {
        int(match.group(1))
        for line in hierarchy_check.stdout.splitlines()
        if (
            match := re.fullmatch(
                r".*noc_segmented_mesh4x4.*?/gen_nodes\[(\d+)\]\.u_router",
                line.strip(),
            )
        )
    }
    if router_nodes != set(range(16)):
        raise ValueError(
            "direct mesh hierarchy must retain router instances 0 through 15, "
            f"found {sorted(router_nodes)}"
        )
    subprocess.run(
        [
            yosys,
            "-q",
            "-p",
            "read_verilog -sv "
            + " ".join(str(path) for path in staged_paths[:2])
            + "; hierarchy -check -top noc_segmented_mesh_router "
            + "-chparam ENABLE_DEBUG_COUNTERS 0; proc; flatten; opt; "
            + "select -assert-none "
            + "r:accepted_flit_count r:forwarded_flit_count "
            + "r:input_stall_cycles r:output_stall_cycles "
            + "r:arbitration_contention_cycles r:max_input_occupancy "
            + "r:route_flit_count",
        ],
        check=True,
        cwd=REPO_ROOT,
    )
    return {
        "required_perimeter_um": required_perimeter_um,
        "available_perimeter_um": available_perimeter_um,
        "minimum_square_side_um": minimum_side_um,
        "perimeter_margin_um": available_perimeter_um - required_perimeter_um,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--verilog-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.config, args.verilog_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
