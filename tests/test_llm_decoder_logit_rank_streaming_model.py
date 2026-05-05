import json
from pathlib import Path

from npu.eval.model_llm_decoder_logit_rank_streaming import (
    build_report,
    simulate_streaming_hierarchy,
)


def test_streaming_hierarchy_cycle_model_tracks_fifo_depth() -> None:
    sim = simulate_streaming_hierarchy(
        vocab_size=16,
        producer_lanes=4,
        producer_latency_cycles=1,
        producer_ii_cycles=1,
        local_ranker_latency_cycles=2,
        local_ranker_ii_cycles=1,
        local_top_k=2,
        global_merge_latency_cycles=1,
        global_merge_ii_cycles=2,
        candidate_fifo_depth_groups=1,
    )

    assert sim["tile_count"] == 4
    assert sim["total_candidates_emitted"] == 8
    assert sim["local_last_done_cycle"] == 6
    assert sim["global_last_done_cycle"] == 10
    assert sim["required_fifo_depth_groups"] == 2
    assert not sim["fifo_capacity_ok"]


def test_logit_rank_streaming_report_compares_flat_and_hierarchy(tmp_path: Path) -> None:
    ppa = tmp_path / "rank_ppa.json"
    ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.0,
                            "die_area": 10.0,
                            "total_power_mw": 0.1,
                        },
                    },
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k4_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 4.0,
                            "die_area": 20.0,
                            "total_power_mw": 0.2,
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        vocab_size=32,
        producer_lanes=8,
        top_k=4,
        global_merge_ii_cycles_list=[1, 2],
        candidate_fifo_depth_groups=8,
    )

    assert report["model"] == "decoder_logit_rank_streaming_hierarchy_v1"
    assert len(report["flat_measured_ranker_points"]) == 2
    assert len(report["hierarchical_streaming_alternatives"]) == 2
    assert report["flat_measured_ranker_points"][0]["lanes"] == 8
    fast = report["hierarchical_streaming_alternatives"][0]
    assert fast["merge_variant"] == "merge_ii_1"
    assert fast["fifo_capacity_ok"]
    assert fast["timing"]["latency_us_per_token"] == 0.044
    assert fast["buffered_baseline"]["rank_after_materialization_cycles"] == 14
    assert fast["buffered_baseline"]["overlap_recovered_cycles"] == 3
    assert fast["traffic"]["traffic_reduction_vs_materialized"] == -0.125
    assert fast["equivalence_contract"]["stream_contract"] == "LogitTileStream/CandidateStream ready-valid v1"
    assert report["recommendation"]["architecture"] in {
        "flat_measured_ranker_scan",
        "hierarchical_streaming_local_rank_global_merge",
    }
    assert len(report["overlap_traffic_sweep"]) == 2
    assert report["overlap_recommendation"]["sweep_key"] == "w8_k4_prodii1_mergeii1_fifo8"


def test_logit_rank_streaming_report_uses_measured_candidate_merge_ppa(tmp_path: Path) -> None:
    rank_ppa = tmp_path / "rank_ppa.json"
    rank_ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k4_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.0,
                            "die_area": 10.0,
                            "total_power_mw": 0.1,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    merge_ppa = tmp_path / "merge_ppa.json"
    merge_ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": (
                                "runs/designs/activations/trials/trial_001/"
                                "candidate_stream_merge_fifo_k4_l16_t16_d8_wrapper/metrics.csv"
                            ),
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 5.0,
                            "die_area": 40.0,
                            "total_power_mw": 0.4,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=rank_ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=merge_ppa,
        vocab_size=32,
        producer_lanes=8,
        top_k=4,
        global_merge_ii_cycles_list=[1],
        candidate_fifo_depth_groups=8,
    )

    row = report["hierarchical_streaming_alternatives"][0]
    assert row["timing"]["clock_ns"] == 5.0
    assert row["candidate_merge_fifo_point"]["metrics_csv"].endswith(
        "candidate_stream_merge_fifo_k4_l16_t16_d8_wrapper/metrics.csv"
    )
    assert row["component_ppa_metrics"]["estimated_total_die_area"] == 50.0
    assert row["component_ppa_metrics"]["estimated_total_power_mw"] == 0.5
    assert row["component_ppa_metrics"]["clock_source"] == "max(local_ranker, candidate_merge_fifo)"
    assert (
        "producer stall cycles"
        in row["equivalence_contract"]["perf_sim_observables"]
    )


def test_logit_rank_streaming_report_adds_memory_hierarchy_terms(tmp_path: Path) -> None:
    ppa = tmp_path / "rank_ppa.json"
    ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.0,
                            "die_area": 10.0,
                            "total_power_mw": 0.1,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        vocab_size=64,
        producer_lanes=8,
        top_k=1,
        global_merge_ii_cycles_list=[1],
        candidate_fifo_depth_groups=16,
        memory_bandwidth_bytes_per_cycle=8.0,
        sram_read_energy_pj_per_byte=1.0,
        sram_write_energy_pj_per_byte=2.0,
        noc_hops=2,
        noc_energy_pj_per_byte_hop=0.5,
    )

    flat = report["flat_measured_ranker_points"][0]
    streaming = report["hierarchical_streaming_alternatives"][0]
    assert report["memory_hierarchy_model"]["source"] == "planning_default_not_literature_backed"
    assert flat["memory_hierarchy"]["total_bytes"] == 256
    assert streaming["memory_hierarchy"]["total_bytes"] == 68
    assert streaming["memory_hierarchy"]["total_memory_energy_nj"] == 0.172
    assert report["memory_traffic_recommendation"]["sweep_key"] == streaming["sweep_key"]
    assert (
        streaming["traffic"]["streaming_candidate_memory_bytes"]
        < flat["memory_hierarchy"]["total_bytes"]
    )


def test_logit_rank_streaming_overlap_sweep_varies_producer_and_fifo(tmp_path: Path) -> None:
    ppa = tmp_path / "rank_ppa.json"
    ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r8_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 3.0,
                            "die_area": 10.0,
                            "total_power_mw": 0.1,
                        },
                    },
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r16_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 5.0,
                            "die_area": 16.0,
                            "total_power_mw": 0.2,
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        vocab_size=64,
        producer_lanes=8,
        top_k=1,
        global_merge_ii_cycles_list=[1, 2],
        producer_lanes_list=[8, 16],
        producer_ii_cycles_list=[1, 2],
        candidate_fifo_depth_groups_list=[1, 16],
    )

    assert len(report["overlap_traffic_sweep"]) == 16
    assert {row["producer_lanes"] for row in report["overlap_traffic_sweep"]} == {8, 16}
    assert any(not row["fifo_capacity_ok"] for row in report["overlap_traffic_sweep"])
    assert report["overlap_recommendation"]["traffic_reduction_vs_materialized"] > 0
