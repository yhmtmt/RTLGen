import pytest

from npu.eval.probe_attention_decode_score_multivalue_service_workload_correspondence import (
    DIVIDER_LANES,
    FINAL_PARTIAL_TOKENS,
    PROJECTED_WINDOWS,
    _affine_proof,
    build_report,
)


def test_workload_correspondence_proves_bounded_rtl_and_projects_affinely() -> None:
    report = build_report()

    assert report["passed"] is True
    assert report["workload"]["windows_per_head"] == PROJECTED_WINDOWS == 5462
    assert report["workload"]["final_partial_tokens"] == FINAL_PARTIAL_TOKENS == 8
    assert [row["divider_lanes"] for row in report["lane_reports"]] == list(DIVIDER_LANES)
    for lane in report["lane_reports"]:
        proof = lane["affine_recurrence_proof"]
        assert proof["measured_service_span_cycles"] == [1051, 2127, 3203, 4279]
        assert proof["counter_deltas"] == [1076, 1076, 1076]
        assert all(row["all_modeled_counters_match_rtl"] for row in lane["bounded_rtl_cases"])
        assert all(row["service_cycle_counter_matches_affine_model"] for row in lane["bounded_rtl_cases"])
        assert all(
            row["finalizer_busy_span_temporal_cycles"] == lane["final_drain_temporal_cycles"]
            for row in lane["bounded_rtl_cases"]
        )
        assert lane["tail_rtl_case"]["block_counts"] == [[3, 3, 3, 1]]
        assert lane["tail_rtl_case"]["summary"]["refills"] == 160
        assert lane["tail_rtl_case"]["summary"]["finalizer_completed"] == 16
        assert lane["state_clear_reuse_rtl_case"]["summary"]["temporal_heads"] == 2
        assert lane["state_clear_reuse_rtl_case"]["summary"]["finalizer_completed"] == 32
        assert lane["tail_adjustment_used_in_projection"] is False
        assert lane["projection"]["service_cycles_per_head"] == 1051 + 5461 * 1076


def test_affine_proof_fails_closed_on_non_affine_counter_deltas() -> None:
    rows = [{"service_span_cycles": value} for value in (10, 20, 31, 41)]
    with pytest.raises(RuntimeError, match="non-affine"):
        _affine_proof(rows)
