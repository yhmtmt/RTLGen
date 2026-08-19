from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_sram_packet_adapter_tb.sv"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


RTL_SOURCES = [
    RTL / "noc_ready_valid_fifo.sv",
    RTL / "noc_segmented_mesh_router.sv",
    RTL / "noc_segmented_mesh4x4.sv",
    RTL / "noc_sram_packet_endpoint.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_packet_bridge.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv",
]


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_finite_sram_adapter_exact_roundtrip_through_real_mesh(tmp_path: Path) -> None:
    simv = tmp_path / "stats_once_exact_sram_packet_adapter.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "local_reducer_aggregate_stats_once_exact_sram_packet_adapter_tb",
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
        timeout=60,
    )
    assert "PASS stats_once_exact_sram_packet_adapter" in run.stdout
    assert "flits=167" in run.stdout
    assert "packets=21" in run.stdout
    assert "beats=128" in run.stdout
    assert "source_max_slots=2" in run.stdout
    assert "destination_max_slots=2" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_finite_sram_adapter_yosys_retains_two_packet_srams(tmp_path: Path) -> None:
    yosys = str(_tool("yosys"))
    netlist = tmp_path / "stats_once_exact_sram_packet_adapter.json"
    subprocess.run(
        [
            yosys,
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + "; hierarchy -check -top "
            + "local_reducer_aggregate_stats_once_exact_sram_packet_adapter; "
            + "proc; memory_dff; memory_collect; check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    design = json.loads(netlist.read_text())
    adapter = design["modules"][
        "local_reducer_aggregate_stats_once_exact_sram_packet_adapter"
    ]
    packet_sram_instances = [
        cell
        for cell in adapter["cells"].values()
        if "local_reducer_aggregate_stats_once_exact_packet_sram" in cell["type"]
    ]
    assert len(packet_sram_instances) == 2

    packet_sram_modules = [
        module
        for name, module in design["modules"].items()
        if "local_reducer_aggregate_stats_once_exact_packet_sram" in name
    ]
    assert len(packet_sram_modules) == 1
    memory_cells = [
        cell
        for cell in packet_sram_modules[0]["cells"].values()
        if cell["type"] == "$mem_v2"
    ]
    assert len(memory_cells) == 1
    assert memory_cells[0]["parameters"]["SIZE"] == "00000000000000000000000000010000"
    assert memory_cells[0]["parameters"]["WIDTH"] == "00000000000000000000000100000000"
