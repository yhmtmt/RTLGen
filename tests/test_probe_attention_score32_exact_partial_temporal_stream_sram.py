import shutil

import pytest

from npu.eval.probe_attention_score32_exact_partial_temporal_stream_sram import (
    build_report,
)


def _sim_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def test_two_heads_three_windows_match_exactly_under_backpressure() -> None:
    if not _sim_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(stress_interfaces=True)

    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert report["summary"]["input_accepted"] == 96
    assert report["summary"]["merge_completed"] == 64
    assert report["summary"]["emitted"] == 32
    assert report["summary"]["completed_heads"] == 2
    assert report["summary"]["output_stalls"] > 0
    assert report["state_memory"]["requests"] == 192
    assert report["state_memory"]["reads"] == 96
    assert report["state_memory"]["responses"] == 96
    assert report["state_memory"]["writes"] == 96
    assert report["state_memory"]["protocol_error"] == 0
    assert report["summary"]["protocol_error"] == 0


def test_order_violation_fails_closed() -> None:
    if not _sim_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(order_violation=True)

    assert report["passed"] is True
    assert report["observed_rows"] == []
    assert report["summary"]["emitted"] == 0
    assert report["summary"]["protocol_error"] == 1
    assert report["state_memory"]["protocol_error"] == 0


def test_last_semantic_violation_fails_closed() -> None:
    if not _sim_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(protocol_violation=True)

    assert report["passed"] is True
    assert report["observed_rows"] == []
    assert report["summary"]["emitted"] == 0
    assert report["summary"]["protocol_error"] == 1
    assert report["state_memory"]["requests"] == 0
