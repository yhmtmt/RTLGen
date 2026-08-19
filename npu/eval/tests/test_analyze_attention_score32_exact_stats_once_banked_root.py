from __future__ import annotations

from npu.eval.analyze_attention_score32_exact_stats_once_banked_root import (
    build_report,
    render_markdown,
)


def test_report_keeps_b4_b8_b15_until_macro_ppa() -> None:
    report = build_report()

    assert report["area_floor_point"] == {
        "physical_banks": 4,
        "fakeram45_64x32_macros": 32,
        "root_delivery_span_cycles": 2939,
        "full_chain_final_cycle": 3077,
        "latency_increase_vs_15_banks_pct": 17.442748,
        "normalized_component_throughput_vs_15_banks": 0.851479,
        "bit_exact": True,
    }
    assert report["pareto_candidate_banks"] == [4, 8, 15]
    assert report["selection_status"]["status"] == "awaiting_macro_ppa"
    assert report["selection_status"]["macro_reduction_vs_15_banks_pct"] == 73.333333
    assert report["selection_status"]["b8_latency_increase_vs_15_banks_pct"] == 8.969466
    assert report["rtl_validation"]["validated_physical_banks"] == [2, 4, 8, 15]
    assert report["rtl_validation"]["bit_exact"] is True
    assert "Precision is unchanged" in report["limitations"][3]


def test_markdown_keeps_noncomparable_metrics_in_separate_columns() -> None:
    markdown = render_markdown(build_report())

    assert "## Registered-SRAM Full-Chain RTL" in markdown
    assert "| 4 | 32 | 2939 | 3077 | +17.442748% | 0.851479 |" in markdown
    assert "| 8 | 64 | 2733 | 2855 | +8.969466% | 0.917688 |" in markdown
    assert "B4 minimizes SRAM count" in markdown
    assert "## Full-Chain RTL Validation" in markdown
    assert "B2 is dominated by B4" in markdown
