from __future__ import annotations

import shutil
import subprocess
import re
from pathlib import Path

import pytest

from npu.sim.perf.attention_shared_sram_k_window_scheduler import (
    SharedSramKWindowScheduler,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl/attention_shared_sram_k_window_scheduler.sv"
TB = REPO_ROOT / "tests/attention_shared_sram_k_window_scheduler_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


pytestmark = pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)


def _run(tmp_path: Path, *plusargs: str) -> subprocess.CompletedProcess[str]:
    sim = tmp_path / "k-window.vvp"
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "attention_shared_sram_k_window_scheduler_tb",
            "-o",
            str(sim),
            str(RTL),
            str(TB),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return subprocess.run(
        [_tool("vvp"), str(sim), *plusargs],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_ideal_17_bank_double_buffer_sustains_compute_after_fill(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert "PASS k_window backpressure=0 requests=1024 responses=1024 compute=128" in result.stdout
    assert "max_compute_interval=1" in result.stdout
    observed = [
        tuple(int(value) for value in match.groups())
        for match in re.finditer(
            r"TRACE group=(\d+) first_req=(\d+) last_req=(\d+) "
            r"compute_start=(\d+) compute_end=(\d+)",
            result.stdout,
        )
    ]
    reference = SharedSramKWindowScheduler(response_latency=2).run().group_traces
    assert len(observed) == len(reference)
    rtl_origin = observed[0][1]
    for row, expected in zip(observed, reference):
        group, first_req, last_req, compute_start, compute_end = row
        assert group == expected.group_index
        assert last_req - first_req + 1 == len(expected.issue_cycles)
        assert compute_start - rtl_origin == expected.compute_start_cycle
        assert compute_end - rtl_origin == expected.compute_end_cycle


def test_independent_bank_and_compute_backpressure_preserve_exact_data(tmp_path: Path) -> None:
    result = _run(tmp_path, "+BACKPRESSURE")
    assert "PASS k_window backpressure=1 requests=1024 responses=1024 compute=128" in result.stdout
    assert "request_stalls=" in result.stdout
    assert "compute_stalls=" in result.stdout


def test_malformed_response_metadata_fails_closed(tmp_path: Path) -> None:
    result = _run(tmp_path, "+MALFORMED")
    assert "PASS k_window malformed_response" in result.stdout


def test_rtl_has_two_concrete_16kib_windows_and_wide_compute_boundary() -> None:
    rtl = RTL.read_text(encoding="utf-8")
    assert "reg [1023:0] buffer_mem [0:(2*WORDS_PER_GROUP)-1]" in rtl
    assert "output wire [(WORDS_PER_GROUP*64)-1:0] compute_k_beats" in rtl
    assert "response_batch_error" in rtl
    assert "issued_bitmap_q" in rtl
