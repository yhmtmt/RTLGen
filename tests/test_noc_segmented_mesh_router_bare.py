from __future__ import annotations

import json
from pathlib import Path

from npu.eval.check_noc_segmented_mesh_router_bare_guard import check
from npu.rtlgen.stage_noc_segmented_mesh_router_bare import SOURCES, stage


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bare_router_staging_is_canonical_and_synthesizable(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "top_name": "noc_segmented_mesh_router_node5",
                "segmented_mesh_router_bare": {
                    "node": 5,
                    "x_coord": 1,
                    "y_coord": 1,
                    "data_bits": 256,
                    "virtual_channels": 4,
                    "fifo_depth": 4,
                    "ports": 5,
                },
            }
        ),
        encoding="utf-8",
    )
    verilog_dir = tmp_path / "verilog"
    staged = stage(config, verilog_dir)

    assert [path.name for path in staged] == list(SOURCES)
    for name in SOURCES:
        assert (verilog_dir / name).read_bytes() == (
            REPO_ROOT / "npu" / "sim" / "rtl" / name
        ).read_bytes()
    check(config, verilog_dir)
