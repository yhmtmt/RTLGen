#!/usr/bin/env python3
"""Stage the canonical node-5 router hierarchy for direct physical implementation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO_ROOT / "npu" / "sim" / "rtl"
SOURCES = (
    "noc_ready_valid_fifo.sv",
    "noc_segmented_mesh_router.sv",
    "noc_segmented_mesh_router_node5.sv",
)


def stage(config_path: Path, out_dir: Path) -> list[Path]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("top_name") != "noc_segmented_mesh_router_node5":
        raise ValueError("bare router top_name must be noc_segmented_mesh_router_node5")
    profile = config.get("segmented_mesh_router_bare")
    if not isinstance(profile, dict):
        raise ValueError("segmented_mesh_router_bare must be an object")
    if profile.get("node") != 5 or profile.get("x_coord") != 1 or profile.get("y_coord") != 1:
        raise ValueError("bare router profile must identify node 5 at coordinate (1,1)")

    out_dir.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for name in SOURCES:
        destination = out_dir / name
        shutil.copyfile(SOURCE_DIR / name, destination)
        staged.append(destination)
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    stage(args.config, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
