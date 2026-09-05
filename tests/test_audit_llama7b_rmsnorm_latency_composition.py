from __future__ import annotations

from pathlib import Path

from npu.eval.audit_llama7b_rmsnorm_latency_composition import build_report, render_markdown


def test_rmsnorm_latency_composition_is_fail_closed(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text("{}", encoding="utf-8")
    baseline = {
        "diagnosis": {
            "current_recommended_candidate": "score32",
            "score32_latency_us": 10000.0,
            "score32_token_throughput_per_s": 100.0,
        }
    }
    baseline_path.write_text(__import__("json").dumps(baseline), encoding="utf-8")
    report = build_report(baseline, baseline_path=baseline_path)

    assert report["rmsnorm_contract"]["rows_per_token"] == 65
    assert report["rmsnorm_contract"]["service_cycles_per_token"] == 117000
    assert report["promotion_gate_pass"] is False
    serialized_10ns = next(
        row for row in report["rows"] if row["clock_period_ns"] == 10.0 and row["hidden_fraction"] == 0.0
    )
    assert serialized_10ns["raw_rmsnorm_latency_us"] == 1170.0
    assert serialized_10ns["composed_latency_us"] == 11170.0
    fully_hidden = next(
        row for row in report["rows"] if row["clock_period_ns"] == 18.0 and row["hidden_fraction"] == 1.0
    )
    assert fully_hidden["composed_latency_us"] == 10000.0
    markdown = render_markdown(report)
    assert "pending_routed_ppa" in markdown
    assert "117000" in markdown
