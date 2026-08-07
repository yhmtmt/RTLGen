import shutil

import pytest

from npu.eval.probe_attention_decode_score_multivalue_service_temporal_cdc import (
    build_report,
)


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


@pytest.mark.parametrize(
    ("service_period_ns", "temporal_period_ns"),
    [(10.0, 7.0), (7.0, 10.0)],
)
def test_real_service_two_windows_cross_nonharmonic_clocks_exactly(
    service_period_ns: float,
    temporal_period_ns: float,
) -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(
        service_period_ns=service_period_ns,
        temporal_period_ns=temporal_period_ns,
    )

    assert report["passed"] is True
    assert report["observed_rows"] == report["expected_rows"]
    assert len(report["observed_rows"]) == 16
    assert report["summary"]["second_refused"] > 0
    assert (
        report["summary"]["second_accept"]
        > report["summary"]["first_terminal"]
    )
    assert report["summary"]["stable"] == 1
    assert report["summary"]["cdc_accepted"] == 32
    assert report["summary"]["cdc_emitted"] == 32
    assert report["summary"]["temporal_inputs"] == 32
    assert report["summary"]["temporal_emitted"] == 16
    assert report["summary"]["temporal_heads"] == 1
    assert report["summary"]["output_stalls"] > 0
    assert report["summary"]["protocol_error"] == 0


def test_service_metadata_mismatch_fails_before_cdc_write() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(mismatch_metadata=True)

    assert report["passed"] is True
    assert report["observed_rows"] == []
    assert report["summary"]["wrapper_error"] == 1
    assert report["summary"]["cdc_accepted"] == 0
    assert report["summary"]["temporal_inputs"] == 0
    assert report["summary"]["service_error"] == 0
    assert report["summary"]["temporal_error"] == 0
    assert report["summary"]["protocol_error"] == 1
