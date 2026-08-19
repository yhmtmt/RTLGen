from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
TB = REPO_ROOT / (
    "tests/local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric_b4_tb.sv"
)
TOP = "local_reducer_aggregate_stats_once_exact_shared_root_storage_fabric"
TB_TOP = TOP + "_b4_tb"


def _tool(name: str) -> str | None:
    path = shutil.which(name)
    if path is not None:
        return path
    fallback = Path("/oss-cad-suite/bin") / name
    return str(fallback) if fallback.exists() else None


RTL_SOURCES = [
    RTL / "local_reducer_aggregate_stats_once_exact_sram_packet_adapter.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter.sv",
]
FULL_ROOT_TB = REPO_ROOT / (
    "tests/local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter_tb.sv"
)
FULL_ROOT_SOURCES = [
    RTL / "noc_ready_valid_fifo.sv",
    RTL / "noc_segmented_mesh_router.sv",
    RTL / "noc_segmented_mesh4x4.sv",
    RTL / "noc_sram_packet_endpoint.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_packet_bridge.sv",
    RTL / "local_reducer_aggregate_stats_once_exact_codec.sv",
    *RTL_SOURCES,
]


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_b4_shared_storage_exact_roundtrip(tmp_path: Path) -> None:
    simv = tmp_path / "shared_root_storage_b4.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            TB_TOP,
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
    assert "PASS shared_root_storage_b4" in run.stdout
    assert "canonical_beats=1920" in run.stdout
    assert "flits=2505" in run.stdout
    assert "packets=315" in run.stdout
    assert "exact_outputs=2505" in run.stdout
    assert "overwrite_errors=0" in run.stdout
    assert "independent_backpressure=1" in run.stdout


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_b4_root_adapter_exact_roundtrip_through_real_mesh(tmp_path: Path) -> None:
    simv = tmp_path / "shared_root_b4_mesh.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-DSHARED_ROOT_PHYSICAL_BANKS=4",
            "-s",
            "local_reducer_aggregate_stats_once_exact_shared_root_rx_adapter_tb",
            "-o",
            str(simv),
            *[str(path) for path in FULL_ROOT_SOURCES],
            str(FULL_ROOT_TB),
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
        timeout=90,
    )
    assert "PASS shared_root_stats_once sources=15" in run.stdout
    assert "beats=1920" in run.stdout
    assert "flits=2505" in run.stdout
    assert "packets=315" in run.stdout
    assert "descriptors=315" in run.stdout
    assert "completions=315" in run.stdout
    assert "replays=315" in run.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_b4_shared_storage_has_four_64x256_banks(tmp_path: Path) -> None:
    netlist = tmp_path / "shared_root_storage_b4.json"
    subprocess.run(
        [
            str(_tool("yosys")),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + f"; chparam -set PHYSICAL_BANKS 4 {TOP}; "
            + f"hierarchy -check -top {TOP}; proc; memory_dff; memory_collect; "
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
    bank_cells = [
        cell
        for cell in top["cells"].values()
        if "shared_root_bank_memory" in cell["type"]
    ]
    assert len(bank_cells) == 4

    bank_modules = [
        module
        for name, module in design["modules"].items()
        if "shared_root_bank_memory" in name
    ]
    assert len(bank_modules) == 1
    mem_cells = [
        cell
        for cell in bank_modules[0]["cells"].values()
        if cell["type"] == "$mem_v2"
    ]
    assert len(mem_cells) == 1
    assert int(mem_cells[0]["parameters"]["SIZE"], 2) == 64
    assert int(mem_cells[0]["parameters"]["WIDTH"], 2) == 256
