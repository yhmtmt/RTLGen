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


def test_logit_rank_streaming_report_derives_sram_energy_from_metrics_json(tmp_path: Path) -> None:
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
    sram_metrics = tmp_path / "sram_metrics.json"
    sram_metrics.write_text(
        json.dumps(
            {
                "arch": "unit-test.yml",
                "id": "unit_test_sram",
                "instances": [
                    {
                        "instance": {
                            "name": "test_sram",
                            "pdk": "sky130",
                            "tech_node_nm": 130,
                            "word_size_bytes": 4,
                        },
                        "estimated": True,
                        "metrics": {
                            "area_um2": 100.0,
                            "access_time_ns": 2.0,
                            "read_energy_pj": 8.0,
                            "write_energy_pj": 12.0,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        sram_metrics_json_path=sram_metrics,
        vocab_size=8,
        producer_lanes=8,
        top_k=1,
        global_merge_ii_cycles_list=[1],
        candidate_fifo_depth_groups=16,
        memory_bandwidth_bytes_per_cycle=64.0,
        sram_read_energy_pj_per_byte=0.05,
        sram_write_energy_pj_per_byte=0.07,
        noc_hops=0,
    )

    flat = report["flat_measured_ranker_points"][0]
    assert report["inputs"]["sram_metrics_json_path"] == str(sram_metrics)
    assert report["inputs"]["effective_sram_read_energy_pj_per_byte"] == 2.0
    assert report["inputs"]["effective_sram_write_energy_pj_per_byte"] == 3.0
    assert report["memory_hierarchy_model"]["source"] == "sram_metrics_json_plus_planning_noc"
    assert report["memory_hierarchy_model"]["sram"]["source_path"] == str(sram_metrics)
    assert flat["memory_hierarchy"]["source"] == "sram_metrics_json_plus_planning_noc"
    assert flat["memory_hierarchy"]["sram_energy_nj"] == 0.08


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


def test_logit_rank_streaming_overlap_sweep_varies_vocab_size(tmp_path: Path) -> None:
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
        global_merge_ii_cycles_list=[1],
        vocab_size_list=[64, 128],
        producer_lanes_list=[8, 16],
        producer_ii_cycles_list=[1],
        candidate_fifo_depth_groups_list=[16],
    )

    assert len(report["overlap_traffic_sweep"]) == 4
    assert {row["vocab_size"] for row in report["overlap_traffic_sweep"]} == {64, 128}
    assert all(row["sweep_key"].startswith("v") for row in report["overlap_traffic_sweep"])
    assert [row["vocab_size"] for row in report["scale_stability_summary"]] == [64, 128]
    assert report["sweep_recommendation_scope"]["vocab_size"] == 64
    assert report["memory_traffic_recommendation"]["sweep_key"].startswith("v64_")
    assert report["inputs"]["vocab_size_list"] == [64, 128]


def test_logit_rank_streaming_report_keeps_boundary_diagnostic_separate(tmp_path: Path) -> None:
    rank_ppa = tmp_path / "rank_ppa.json"
    rank_ppa.write_text(
        json.dumps(
            {
                "proposals": [
                    {
                        "metrics_ref": {
                            "metrics_csv": "runs/designs/activations/logit_rank_r32_l16_k1_wrapper/metrics.csv",
                            "status": "ok",
                        },
                        "metric_summary": {
                            "critical_path_ns": 10.0,
                            "die_area": 32.0,
                            "total_power_mw": 0.32,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    metrics_csv = (
        tmp_path
        / "runs"
        / "designs"
        / "activations"
        / "logit_rank_r128_l16_k1_wrapper"
        / "metrics.csv"
    )
    metrics_csv.parent.mkdir(parents=True)
    metrics_csv.write_text(
        "\n".join(
            [
                "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path",
                (
                    'logit_rank_r128_l16_k1_wrapper,nangate45,h,87f21ce3,'
                    'pinbound_540,ok,60.216,291600.0,3.72,'
                    '"{""DIE_AREA"": ""0 0 540 540"", ""CORE_AREA"": ""20 20 520 520""}",'
                    'runs/designs/activations/logit_rank_r128_l16_k1_wrapper/work/87f21ce3/result.json'
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    boundary_ppa = tmp_path / "boundary_ppa.json"
    boundary_ppa.write_text(
        json.dumps(
            {
                "item_id": "l1_decoder_logit_rank_r128_k1_pin_perimeter_bound_v1",
                "source_refs": {"trial_metrics_csvs": [str(metrics_csv)]},
            }
        ),
        encoding="utf-8",
    )

    report = build_report(
        rank_ppa_path=rank_ppa,
        scale_ppa_path=None,
        candidate_merge_ppa_path=None,
        boundary_ppa_path=boundary_ppa,
        vocab_size=128,
        producer_lanes=128,
        top_k=1,
        global_merge_ii_cycles_list=[1],
        producer_lanes_list=[64, 128],
        producer_interface_focus_lanes=[64, 128],
        top_k_list=[1],
        candidate_fifo_depth_groups_list=[16],
    )

    comparison = report["boundary_sensitivity"]["comparisons"][0]
    assert comparison["boundary_die_perimeter_um"] == 2160.0
    assert comparison["boundary_padded_die_area_um2"] == 291600.0
    assert comparison["boundary_critical_path_ns"] == 60.216
    assert comparison["normal_model_critical_path_ns"] == 14.0
    assert "Do not charge" in comparison["policy"]
    assert report["hierarchical_streaming_alternatives"][0]["local_ranker_point"]["source"].endswith(
        "#scaled_nearest_lane"
    )
    interface = report["producer_integrated_interface"]
    assert interface["scope"] == "producer_integrated_ready_valid_ranker_interface"
    assert interface["focus_lanes"] == [64, 128]
    assert "top_level_scalar_logit_pin_count" in interface["excluded_from_main_cost"]
    assert "valid mask per accepted tile" in interface["equivalence_observables"]
    assert interface["boundary_diagnostics"][0]["critical_path_ratio_vs_normal_model"] == 4.301143
    assert {row["producer_lanes"] for row in interface["summary_rows"]} == {64, 128}
