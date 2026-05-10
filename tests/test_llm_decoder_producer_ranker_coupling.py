from pathlib import Path

from npu.eval.estimate_llm_decoder_producer_ranker_coupling import build_coupling_report


def test_producer_service_derives_integer_ii_from_compute_and_memory() -> None:
    report = build_coupling_report(
        mode="producer_service",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    row = report["producer_service_sweep"][0]
    assert row["compute_cycles_per_tile"] == 1
    assert row["weight_cycles_per_tile"] == 64
    assert row["producer_ii_cycles"] == 64
    assert row["service_limiter"] == "weight_memory"
    assert report["coupled_ranker_sweep"] == []


def test_coupled_noc_reports_ranker_rows(tmp_path: Path) -> None:
    report = build_coupling_report(
        mode="coupled_noc",
        rank_ppa_path=None,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=None,
        sram_metrics_json_path=None,
        vocab_size_list=[256],
        hidden_size_list=[64],
        producer_lanes_list=[64],
        macs_per_cycle_list=[4096],
        memory_bandwidth_bytes_per_cycle_list=[128.0],
        memory_share_list=[1.0, 0.5],
        top_k_list=[1],
        weight_bits=16,
        activation_bits=16,
        clock_ns=1.0,
    )

    assert report["coupled_ranker_sweep"]
    row = report["coupled_ranker_sweep"][0]
    assert row["producer_lanes"] == 64
    assert row["top_k"] == 1
    assert row["producer_ii_cycles"] >= 1
    assert "ranker_latency_us_per_token" in row
    assert row["coupled_latency_us_per_token"] >= row["producer_latency_us_per_token"]
    assert report["recommendation"]["coupled_best"] is not None
