from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl"
RTL_SOURCES = [
    RTL / "noc_ready_valid_fifo.sv",
    RTL / "noc_segmented_mesh_router.sv",
    RTL / "noc_segmented_mesh4x4.sv",
    RTL / "noc_sram_packet_endpoint.sv",
    RTL / "noc_sram_packet_mesh4x4.sv",
    RTL / "attention_shared_stream_context_admission.sv",
    RTL / "attention_shared_stream_context_engine.sv",
    RTL / "attention_shared_stream_context_service.sv",
    RTL / "attention_shared_stream_context_service_ppa_activity_harness.sv",
]
TB = REPO_ROOT / "tests/attention_shared_stream_context_service_full_tb.sv"
PASS_RE = re.compile(
    r"PASS shared_stream_full contexts=(?P<contexts>\d+) packets=(?P<packets>\d+) "
    r"flits=(?P<flits>\d+) cycles=(?P<cycles>\d+) fold=(?P<fold>[0-9a-fA-F]+)"
)


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}"
        if Path(f"/oss-cad-suite/bin/{name}").exists()
        else None
    )


@pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)
def test_full_112_context_service_completes_exact_workload(tmp_path: Path) -> None:
    sim = tmp_path / "shared-stream-full.vvp"
    subprocess.run(
        [
            str(_tool("iverilog")),
            "-g2012",
            "-s",
            "attention_shared_stream_context_service_full_tb",
            "-o",
            str(sim),
            *[str(path) for path in RTL_SOURCES],
            str(TB),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=180,
    )
    run = subprocess.run(
        [str(_tool("vvp")), str(sim)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )
    match = PASS_RE.search(run.stdout)
    assert match is not None, run.stdout
    observed = match.groupdict()
    assert int(observed["contexts"]) == 112
    assert int(observed["packets"]) == 7616
    assert int(observed["flits"]) == 60928
    assert int(observed["cycles"]) == 7783
    assert int(observed["fold"], 16) == 0x0000000000000D100000000000000D10
