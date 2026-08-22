from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from npu.sim.perf.attention_shared_sram_k_round_scheduler import (
    SharedSramKRoundScheduler,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
RTL = REPO_ROOT / "npu/sim/rtl/attention_shared_sram_k_round_scheduler.sv"
BANK_RTL = REPO_ROOT / "npu/sim/rtl/attention_shared_sram_k_round_bank.sv"
TB = REPO_ROOT / "tests/attention_shared_sram_k_round_scheduler_tb.sv"


def _tool(name: str) -> str | None:
    return shutil.which(name) or (
        f"/oss-cad-suite/bin/{name}" if Path(f"/oss-cad-suite/bin/{name}").exists() else None
    )


pytestmark = pytest.mark.skipif(
    _tool("iverilog") is None or _tool("vvp") is None,
    reason="iverilog/vvp unavailable",
)


def _run(tmp_path: Path, *plusargs: str) -> subprocess.CompletedProcess[str]:
    sim = tmp_path / "k-round.vvp"
    subprocess.run(
        [
            _tool("iverilog"),
            "-g2012",
            "-s",
            "attention_shared_sram_k_round_scheduler_tb",
            "-o",
            str(sim),
            str(BANK_RTL),
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


def test_ideal_round_scheduler_preserves_exact_data_and_order(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert "PASS k_round backpressure=0 requests=1024 responses=1024 compute=1024" in result.stdout
    assert "max_compute_interval=1" in result.stdout

    observed = [
        tuple(int(value) for value in match.groups())
        for match in re.finditer(
            r"TRACE round=(\d+) first_req=(\d+) compute_start=(\d+) compute_end=(\d+)",
            result.stdout,
        )
    ]
    reference = SharedSramKRoundScheduler(response_latency=2).run().round_traces
    assert len(observed) == len(reference) == 64

    # Simulator reset/command setup adds a constant origin only.  Relative
    # compute timing must match the executable performance model exactly.
    rtl_origin = observed[0][2]
    model_origin = reference[0].compute_start_cycle
    for row, expected in zip(observed, reference):
        linear_round, _first_req, compute_start, compute_end = row
        assert linear_round == expected.linear_round
        assert compute_start - rtl_origin == expected.compute_start_cycle - model_origin
        assert compute_end - rtl_origin == expected.compute_end_cycle - model_origin


def test_round_scheduler_handles_bank_and_compute_backpressure(tmp_path: Path) -> None:
    result = _run(tmp_path, "+BACKPRESSURE")
    assert "PASS k_round backpressure=1 requests=1024 responses=1024 compute=1024" in result.stdout
    assert "request_stalls=" in result.stdout
    assert "compute_stalls=" in result.stdout


def test_round_scheduler_rejects_malformed_response_metadata(tmp_path: Path) -> None:
    result = _run(tmp_path, "+MALFORMED")
    assert "PASS k_round malformed_response" in result.stdout


def test_round_rtl_has_bounded_storage_and_narrow_compute_boundary() -> None:
    rtl = BANK_RTL.read_text(encoding="utf-8") + RTL.read_text(encoding="utf-8")
    assert "module attention_shared_sram_k_round_bank" in rtl
    assert "reg [1023:0] buffer_mem0" in rtl
    assert "reg [1023:0] buffer_mem1" in rtl
    assert "output wire [(BANKS*64)-1:0] compute_k_beats" in rtl
    assert "output wire [BANKS-1:0] compute_word_valid" in rtl
    assert '(* keep = "true" *) reg [1023:0] buffer_mem0' in rtl
    assert '(* keep = "true" *) reg [1023:0] buffer_mem1' in rtl
    assert "response_batch_error" in rtl
