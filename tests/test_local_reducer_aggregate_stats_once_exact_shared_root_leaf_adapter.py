from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter_tb.sv"
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter_tb"
BRIDGE_TOP = "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


RTL_SOURCES = [
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_leaf_adapter.sv",
]


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_shared_root_leaf_adapter_mapping_and_independent_backpressure(
    tmp_path: Path,
) -> None:
    simv = tmp_path / "shared_root_leaf_adapter.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TOP,
            "-o",
            str(simv),
            *[str(path) for path in RTL_SOURCES],
            str(TB),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(simv)],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert "PASS shared_root_leaf_adapter leaves=16 beats_per_leaf=128" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_shared_root_leaf_adapter_has_exactly_fifteen_decoders(
    tmp_path: Path,
) -> None:
    netlist = tmp_path / "shared_root_leaf_adapter.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + f"; hierarchy -check -top {BRIDGE_TOP}; proc; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    design = json.loads(netlist.read_text())
    top = design["modules"][BRIDGE_TOP]
    decoder_cells = [
        cell
        for cell in top["cells"].values()
        if "local_reducer_aggregate_stats_once_exact_decoder" in cell["type"]
    ]
    assert len(decoder_cells) == 15
    assert len(top["ports"]["leaf_valid"]["bits"]) == 16
    assert len(top["ports"]["leaf_command_id"]["bits"]) == 16 * 16
    assert len(top["ports"]["leaf_head_id"]["bits"]) == 16 * 5
    assert len(top["ports"]["leaf_global_max"]["bits"]) == 16 * 32
    assert len(top["ports"]["leaf_exp_sum"]["bits"]) == 16 * 33
    assert len(top["ports"]["leaf_slice"]["bits"]) == 16 * 4
    assert len(top["ports"]["leaf_last"]["bits"]) == 16
    assert len(top["ports"]["leaf_value"]["bits"]) == 16 * 328
