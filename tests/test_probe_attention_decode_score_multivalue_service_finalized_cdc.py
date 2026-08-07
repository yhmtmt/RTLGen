import shutil

import pytest

from npu.eval.probe_attention_decode_score_multivalue_service_finalized_cdc import (
    build_report,
)


def test_real_c1_two_window_full_context_finalization() -> None:
    if not (shutil.which("iverilog") and shutil.which("vvp")):
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(
        service_period_ns=10.0,
        temporal_period_ns=7.0,
        divider_lanes=8,
    )

    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert len(report["observed_rows"]) == 16
    assert report["summary"]["stable"] == 1
    assert report["summary"]["cdc_accepted"] == 32
    assert report["summary"]["cdc_emitted"] == 32
    assert report["summary"]["temporal_emitted"] == 16
    assert report["summary"]["finalizer_accepted"] == 16
    assert report["summary"]["finalizer_completed"] == 16
    assert report["summary"]["protocol_error"] == 0
