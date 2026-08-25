from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.sim.perf.attention_shared_stream_context_service import (
    build_activity_contexts,
    simulate_context_service,
)


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
CONTEXT_RE = re.compile(
    r"TRACE_CONTEXT cycle=(?P<cycle>\d+) wave=(?P<wave>\d+) "
    r"destination=(?P<destination>\d+) source=(?P<source>\d+)"
)
COMPLETION_RE = re.compile(
    r"TRACE_COMPLETION cycle=(?P<cycle>\d+) wave=(?P<wave>\d+) "
    r"destination=(?P<destination>\d+)"
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
    contexts = build_activity_contexts()
    model = simulate_context_service(
        contexts,
        event_candidate_cycles=range(3, 3 + len(contexts)),
        source_sram_request_ready=lambda cycle, endpoint: (
            (cycle & 0x7) ^ (endpoint & 0x7)
        )
        != 0,
        destination_sram_write_ready=lambda cycle, endpoint: (
            (cycle + endpoint) & 0xF
        )
        != 0,
        context_completion_ready=lambda cycle: (cycle & 0x1F) != 0,
    )
    rtl_contexts = [
        tuple(int(match.group(field)) for field in ("cycle", "wave", "destination", "source"))
        for match in CONTEXT_RE.finditer(run.stdout)
    ]
    rtl_completions = [
        tuple(int(match.group(field)) for field in ("cycle", "wave", "destination"))
        for match in COMPLETION_RE.finditer(run.stdout)
    ]
    model_contexts = [
        (row.cycle, row.wave, row.destination, row.source) for row in model.admissions
    ]
    model_completions = [
        (row.cycle, row.wave, row.destination) for row in model.completions
    ]

    assert rtl_contexts == model_contexts
    assert rtl_completions == model_completions
    assert int(observed["contexts"]) == 112
    assert int(observed["packets"]) == 7616
    assert int(observed["flits"]) == 60928
    assert int(observed["cycles"]) == model.cycles == 7783
    assert int(observed["fold"], 16) == model.write_fold == (
        0x0000000000000D100000000000000D10
    )
