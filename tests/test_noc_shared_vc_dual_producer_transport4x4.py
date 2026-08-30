from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = [
    REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/noc_endpoint_vc_injection_arbiter.sv",
    REPO_ROOT / "npu/sim/rtl/noc_shared_vc_dual_producer_transport4x4.sv",
]
TB = REPO_ROOT / "tests/noc_shared_vc_dual_producer_transport4x4_tb.sv"


def _tool(name: str) -> str | None:
    resolved = shutil.which(name)
    bundled = Path("/oss-cad-suite/bin") / name
    return resolved or (str(bundled) if bundled.exists() else None)


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_transport_dual_producer_behavior(tmp_path: Path) -> None:
    executable = tmp_path / "shared-transport.vvp"
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "noc_shared_vc_dual_producer_transport4x4_tb",
            "-o",
            str(executable),
            *[str(path) for path in RTL_SOURCES],
            str(TB),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result = subprocess.run(
        [_tool("vvp"), str(executable)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert "PASS shared transport arbitration, demux, conservation, and failure handling" in result.stdout


@pytest.mark.skipif(_tool("yosys") is None, reason="yosys unavailable")
def test_shared_transport_hierarchy_has_exactly_16_arbiters_and_1_mesh(tmp_path: Path) -> None:
    netlist = tmp_path / "shared-transport.json"
    subprocess.run(
        [
            _tool("yosys"),
            "-q",
            "-p",
            "read_verilog -DSYNTHESIS -sv "
            + " ".join(str(path) for path in RTL_SOURCES)
            + "; hierarchy -check -top noc_shared_vc_dual_producer_transport4x4"
            + "; proc; check; write_json "
            + str(netlist),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    design = json.loads(netlist.read_text(encoding="utf-8"))
    cells = list(
        design["modules"]["noc_shared_vc_dual_producer_transport4x4"]["cells"].values()
    )
    assert sum("noc_endpoint_vc_injection_arbiter" in cell["type"] for cell in cells) == 16
    assert sum("noc_segmented_mesh4x4" in cell["type"] for cell in cells) == 1
