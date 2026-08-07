import shutil

import pytest

from npu.eval.probe_attention_decode_score_multivalue_service_temporal import (
    LOGICAL_COMMAND_ID,
    PHYSICAL_COMMAND_IDS,
    SEQUENCE_ID,
    build_report,
)


def _iverilog_available() -> bool:
    return bool(shutil.which("iverilog") and shutil.which("vvp"))


def test_real_service_two_windows_merge_exactly_and_hold_metadata() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report()

    assert report["passed"] is True
    assert report["physical_command_ids"] == list(PHYSICAL_COMMAND_IDS)
    assert report["logical_sequence_id"] == SEQUENCE_ID
    assert report["logical_command_id"] == LOGICAL_COMMAND_ID
    assert report["observed_rows"] == report["expected_rows"]
    assert len(report["observed_rows"]) == 16
    assert all(row["sequence_id"] == SEQUENCE_ID for row in report["observed_rows"])
    assert all(
        row["command_id"] == LOGICAL_COMMAND_ID for row in report["observed_rows"]
    )
    assert report["summary"]["second_refused"] > 0
    assert (
        report["summary"]["second_accept"]
        > report["summary"]["first_terminal"]
    )
    assert report["summary"]["stable"] == 1
    assert report["summary"]["output_stalls"] > 0
    assert report["summary"]["service_accepted"] == 2
    assert report["summary"]["service_completed"] == 2
    assert report["summary"]["temporal_inputs"] == 32
    assert report["summary"]["temporal_emitted"] == 16
    assert report["summary"]["temporal_heads"] == 1
    assert report["summary"]["protocol_error"] == 0


def test_mismatched_service_metadata_fails_closed() -> None:
    if not _iverilog_available():
        pytest.skip("iverilog/vvp unavailable")

    report = build_report(mismatch_metadata=True)

    assert report["passed"] is True
    assert report["observed_rows"] == []
    assert report["summary"]["wrapper_error"] == 1
    assert report["summary"]["service_error"] == 0
    assert report["summary"]["temporal_error"] == 0
    assert report["summary"]["temporal_inputs"] == 0
    assert report["summary"]["protocol_error"] == 1
