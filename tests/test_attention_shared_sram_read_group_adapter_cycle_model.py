from __future__ import annotations

import pytest

from npu.eval.evaluate_attention_shared_sram_read_group_adapter_frontier import build_report
from npu.sim.perf.attention_shared_sram_read_group_adapter import (
    simulate_shared_sram_read_group_adapter,
)


@pytest.mark.parametrize(
    ("beat_width", "group_slots", "expected_cycles", "requests"),
    (
        (256, 1, 682, 256),
        (256, 2, 346, 256),
        (512, 1, 409, 128),
        (512, 2, 208, 128),
    ),
)
def test_cycle_model_exact_counts(
    beat_width: int,
    group_slots: int,
    expected_cycles: int,
    requests: int,
) -> None:
    result = simulate_shared_sram_read_group_adapter(
        beat_width=beat_width,
        group_slots=group_slots,
    )

    assert result.cycle_count == expected_cycles
    assert result.beat_request_count == requests
    assert result.macro_read_count == 64
    assert result.beat_response_count == requests
    assert result.protocol_error is False
    assert result.access_reduction_proven is True


def test_all_adapter_variants_match_rtl_and_attach_physical_metrics() -> None:
    report = build_report(clock_period_ns=2.0)

    assert report["passed"] is True
    assert len(report["variants"]) == 4
    assert all(row["equivalence_passed"] for row in report["variants"])
    assert report["dimension_winners"] == {
        "adapter_group_service_throughput": "attention_shared_sram_read_group_adapter_w512_s2",
        "adapter_vectorless_total_energy_proxy": "attention_shared_sram_read_group_adapter_w512_s2",
        "adapter_instance_area": "attention_shared_sram_read_group_adapter_w512_s1",
        "precision": "all_variants_exact",
    }
