#!/usr/bin/env python3
"""Reject a bare-router physical source that diverges from the replay hierarchy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DIR = REPO_ROOT / "npu" / "sim" / "rtl"
SOURCE_NAMES = (
    "noc_ready_valid_fifo.sv",
    "noc_segmented_mesh_router.sv",
    "noc_segmented_mesh_router_node5.sv",
)


def check(config_path: Path, verilog_dir: Path) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("top_name") != "noc_segmented_mesh_router_node5":
        raise ValueError("physical and replay top must be noc_segmented_mesh_router_node5")
    profile = config.get("segmented_mesh_router_bare")
    expected = {
        "node": 5,
        "x_coord": 1,
        "y_coord": 1,
        "data_bits": 256,
        "virtual_channels": 4,
        "fifo_depth": 4,
        "ports": 5,
    }
    if profile != expected:
        raise ValueError(f"bare-router profile mismatch: expected {expected}, got {profile}")

    staged_paths: list[Path] = []
    for name in SOURCE_NAMES:
        staged = verilog_dir / name
        canonical = CANONICAL_DIR / name
        if not staged.is_file() or staged.read_bytes() != canonical.read_bytes():
            raise ValueError(f"staged router source differs from canonical replay source: {name}")
        staged_paths.append(staged)

    specialization = (verilog_dir / "noc_segmented_mesh_router_node5.sv").read_text(
        encoding="utf-8"
    )
    if "always" in specialization or specialization.count("noc_segmented_mesh_router #(") != 1:
        raise ValueError("node-5 specialization must be logic-free and instantiate one router")

    yosys = shutil.which("yosys") or "/oss-cad-suite/bin/yosys"
    subprocess.run(
        [
            yosys,
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in staged_paths)
            + "; hierarchy -check -top noc_segmented_mesh_router_node5; proc; check",
        ],
        check=True,
        cwd=REPO_ROOT,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--verilog-dir", type=Path, required=True)
    args = parser.parse_args()
    check(args.config, args.verilog_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
