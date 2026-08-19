from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BRIDGE = REPO_ROOT / "npu/sim/rtl/local_reducer_aggregate_stats_once_exact_packet_bridge.sv"
FIFO = REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv"
ROUTER = REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv"
MESH = REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_packet_mesh_tb.sv"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_stats_once_exact_packet_bridge_real_mesh(tmp_path: Path) -> None:
    simv = tmp_path / "stats_once_exact_packet_mesh.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_stats_once_exact_packet_mesh_tb",
            "-o",
            str(simv),
            str(BRIDGE),
            str(FIFO),
            str(ROUTER),
            str(MESH),
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
        timeout=60,
    )
    assert (
        "PASS local_reducer_aggregate_stats_once_exact_packet_mesh" in run.stdout
    )
    assert "groups=2" in run.stdout
    assert "flits=334" in run.stdout
    assert "packets=42" in run.stdout
    assert "outputs=334" in run.stdout
    assert "tx_clean=2" in run.stdout
    assert "rx_clean=2" in run.stdout
    assert "clean=2" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_stats_once_exact_packet_bridge_yosys_import_process_check() -> None:
    yosys = str(_tool("yosys"))
    for top in (
        "local_reducer_aggregate_stats_once_exact_packet_tx_framer",
        "local_reducer_aggregate_stats_once_exact_packet_rx_deframer",
    ):
        subprocess.run(
            [
                yosys,
                "-q",
                "-p",
                "read_verilog -DSYNTHESIS -sv "
                f"{BRIDGE}; hierarchy -check -top {top}; proc; check",
            ],
            check=True,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
