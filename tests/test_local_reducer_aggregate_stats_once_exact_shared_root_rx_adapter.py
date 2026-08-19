from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / "tests/local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter_tb.sv"
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter"


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
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv",
]


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_shared_root_exact_15_source_mesh_equivalence(tmp_path: Path) -> None:
    simv = tmp_path / "shared_root_stats_once.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            f"{TOP}_tb",
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
    assert "PASS shared_root_stats_once sources=15" in run.stdout
    assert "beats=1920" in run.stdout
    assert "flits=2505" in run.stdout
    assert "packets=315" in run.stdout
    assert "descriptors=315" in run.stdout
    assert "completions=315" in run.stdout
    assert "replays=315" in run.stdout
    assert "root_delivery_span=2505" in run.stdout
    assert "source_mask=7fff" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_shared_root_yosys_has_one_endpoint_and_fifteen_sram_banks(
    tmp_path: Path,
) -> None:
    netlist = tmp_path / "shared_root_stats_once.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + f"; hierarchy -check -top {TOP}; proc; memory_dff; memory_collect; "
            + "check; write_json "
            + str(netlist),
        ],
        check=True,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    design = json.loads(netlist.read_text())
    top = design["modules"][TOP]
    endpoint_cells = [
        cell
        for cell in top["cells"].values()
        if "noc_sram_packet_endpoint" in cell["type"]
    ]
    packet_sram_cells = [
        cell
        for cell in top["cells"].values()
        if "local_reducer_aggregate_stats_once_exact_packet_sram" in cell["type"]
    ]
    deframer_cells = [
        cell
        for cell in top["cells"].values()
        if "local_reducer_aggregate_stats_once_exact_packet_rx_deframer"
        in cell["type"]
    ]
    assert len(endpoint_cells) == 1
    assert len(packet_sram_cells) == 15
    assert len(deframer_cells) == 15

    sram_modules = [
        module
        for name, module in design["modules"].items()
        if name.endswith("local_reducer_aggregate_stats_once_exact_packet_sram")
        or "local_reducer_aggregate_stats_once_exact_packet_sram" in name
    ]
    assert len(sram_modules) == 1
    mem_cells = [
        cell
        for cell in sram_modules[0]["cells"].values()
        if cell["type"] == "$mem_v2"
    ]
    assert len(mem_cells) == 1
    assert mem_cells[0]["parameters"]["SIZE"] == "00000000000000000000000000010000"
    assert mem_cells[0]["parameters"]["WIDTH"] == "00000000000000000000000100000000"
    assert len(packet_sram_cells) * len(mem_cells) == 15
