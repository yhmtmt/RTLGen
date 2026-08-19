from __future__ import annotations

from npu.eval.analyze_attention_score32_exact_stats_once_banked_root import (
    build_report,
    render_markdown,
)


def test_report_selects_four_bank_minimum_macro_floor_point() -> None:
    report = build_report()

    assert report["selected_point"] == {
        "physical_banks": 4,
        "fakeram45_64x32_macros": 32,
        "root_delivery_span_cycles": 2505,
        "replay_drain_cycles": 13,
        "final_replay_cycle": 2533,
        "max_slots_per_source": 2,
        "schedule_iterations": 1,
        "exact_transport": True,
    }
    assert report["selection"]["macro_reduction_vs_15_banks_pct"] == 73.333333
    assert report["selection"]["two_bank_transport_span_penalty_pct"] == 4.91018
    assert report["rtl_validation"]["retained_bank_memories"] == 4
    assert report["rtl_validation"]["full_chain_final_cycle"] == 2613
    assert report["rtl_validation"]["full_chain_latency_increase_pct"] == 0.5
    assert report["rtl_validation"]["bit_exact"] is True
    assert "Precision is unchanged" in report["limitations"][2]


def test_markdown_keeps_noncomparable_metrics_in_separate_columns() -> None:
    markdown = render_markdown(build_report())

    assert "| banks | 64x32 macros | root span cycles | replay drain cycles |" in markdown
    assert "| 4 | 32 | 2505 | 13 | 1 |" in markdown
    assert "Four banks are selected" in markdown
    assert "## Full-Chain RTL Validation" in markdown
    assert "final cycle `2613`" in markdown
