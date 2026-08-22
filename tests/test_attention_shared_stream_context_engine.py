from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RTL_SOURCES = [
    REPO_ROOT / "npu/sim/rtl/noc_ready_valid_fifo.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh_router.sv",
    REPO_ROOT / "npu/sim/rtl/noc_segmented_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_endpoint.sv",
    REPO_ROOT / "npu/sim/rtl/noc_sram_packet_mesh4x4.sv",
    REPO_ROOT / "npu/sim/rtl/attention_shared_stream_context_engine.sv",
]
TB = REPO_ROOT / "tests/attention_shared_stream_context_engine_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


def _run(
    tmp_path: Path,
    *,
    max_packets: int = 68,
    packet_index_w: int = 7,
    context_count: int = 112,
    plusargs: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    sim = tmp_path / ("engine-" + str(max_packets) + ".vvp")
    subprocess.run(
        [_tool("iverilog"), "-g2012", "-s", "attention_shared_stream_context_engine_tb",
         f"-Pattention_shared_stream_context_engine_tb.MAX_PACKETS_PER_CONTEXT={max_packets}",
         f"-Pattention_shared_stream_context_engine_tb.PACKET_INDEX_W={packet_index_w}",
         f"-Pattention_shared_stream_context_engine_tb.TEST_CONTEXT_COUNT={context_count}",
         "-o", str(sim), *[str(path) for path in RTL_SOURCES], str(TB)],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    return subprocess.run([_tool("vvp"), str(sim), *plusargs], cwd=REPO_ROOT,
                          check=True, capture_output=True, text=True, timeout=180)


@pytest.mark.skipif(
    os.environ.get("RTLGEN_RUN_SLOW_RTL") != "1",
    reason="set RTLGEN_RUN_SLOW_RTL=1 for the exhaustive 112-context replay",
)
@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_engine_exact_112_contexts_and_parallel_descriptors(tmp_path: Path) -> None:
    run = _run(tmp_path)
    assert "PASS engine contexts=112 descriptors=7616 flits=60928" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_engine_reduced_packet_smoke(tmp_path: Path) -> None:
    run = _run(tmp_path, max_packets=3, packet_index_w=2, context_count=2)
    assert "PASS engine contexts=2 descriptors=6 flits=48" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_engine_latches_variable_packet_counts_including_over_256(tmp_path: Path) -> None:
    run = _run(tmp_path, max_packets=300, packet_index_w=9, context_count=2,
               plusargs=("+VARIABLE_COUNT_CASE",))
    assert "PASS engine contexts=2 descriptors=260 flits=2080" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_engine_rejects_invalid_command_without_wedging(tmp_path: Path) -> None:
    run = _run(tmp_path, plusargs=("+INVALID_CASE",))
    assert "PASS engine invalid_command_fail_closed" in run.stdout


@pytest.mark.skipif(_tool("iverilog") is None or _tool("vvp") is None, reason="iverilog/vvp unavailable")
def test_shared_stream_engine_issues_sixteen_endpoint_disjoint_descriptors(tmp_path: Path) -> None:
    run = _run(tmp_path, context_count=16, plusargs=("+PARALLEL_CASE",))
    assert "PASS engine parallel_descriptors rx_lead=16 tx=16 rx=16" in run.stdout
