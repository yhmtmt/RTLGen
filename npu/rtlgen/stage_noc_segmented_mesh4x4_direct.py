#!/usr/bin/env python3
"""Stage the canonical direct-port 4x4 mesh hierarchy for physical implementation."""

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
    "noc_segmented_mesh4x4.sv",
    "noc_segmented_mesh4x4_functional.sv",
)


def stage(config_path: Path, out_dir: Path) -> list[Path]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("top_name") != "noc_segmented_mesh4x4_functional":
        raise ValueError("direct mesh top_name must be noc_segmented_mesh4x4_functional")
    profile = config.get("segmented_mesh4x4_direct")
    if not isinstance(profile, dict) or profile.get("nodes") != 16:
        raise ValueError("segmented_mesh4x4_direct must identify sixteen nodes")

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
