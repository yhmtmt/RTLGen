from npu.eval.plan_llm_decoder_producer_ranker_memory_integration import build_report


def test_integration_plan_separates_mac_modules_from_tile_lanes() -> None:
    frontier = {
        "model": "frontier",
        "focus_summary": [
            {
                "label": "gpt2_medium_proxy",
                "sequence_length": 128,
                "hidden_size": 1024,
                "vocab_size": 50257,
                "dominant_component": "output_projection_producer_ranker",
                "producer_choice": {
                    "producer_lanes": 64,
                    "top_k": 1,
                    "memory_share": 1.0,
                    "producer_ii_cycles": 512,
                },
            },
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "hidden_size": 768,
                "vocab_size": 50257,
                "dominant_component": "output_projection_producer_ranker",
                "producer_choice": {
                    "producer_lanes": 64,
                    "top_k": 1,
                    "memory_share": 1.0,
                    "producer_ii_cycles": 384,
                },
            }
        ],
    }
    coupling = {
        "model": "coupling",
        "producer_service_sweep": [
            {
                "scenario": "shared_gemm_stage_serial",
                "hidden_size": 1024,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "macs_per_cycle": 8192,
                "memory_share": 1.0,
                "producer_ii_cycles": 512,
                "compute_cycles_per_tile": 8,
                "weight_cycles_per_tile": 512,
                "hidden_load_cycles": 8,
            },
            {
                "scenario": "shared_gemm_stage_serial",
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "macs_per_cycle": 8192,
                "memory_share": 1.0,
                "producer_ii_cycles": 384,
                "compute_cycles_per_tile": 6,
                "weight_cycles_per_tile": 384,
                "hidden_load_cycles": 6,
            }
        ],
        "coupled_ranker_sweep": [
            {
                "scenario": "shared_gemm_stage_serial",
                "hidden_size": 1024,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "top_k": 1,
                "macs_per_cycle": 8192,
                "memory_share": 1.0,
                "producer_ii_cycles": 512,
                "producer_latency_us_per_token": 401.936,
                "ranker_latency_us_per_token": 6728.322951,
                "coupled_latency_us_per_token": 6728.322951,
                "ranker_fifo_capacity_ok": True,
                "ranker_required_fifo_depth_groups": 1,
                "ranker_candidate_memory_bytes": 6292,
            },
            {
                "scenario": "shared_gemm_stage_serial",
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "top_k": 1,
                "macs_per_cycle": 8192,
                "memory_share": 1.0,
                "producer_ii_cycles": 384,
                "producer_latency_us_per_token": 301.452,
                "ranker_latency_us_per_token": 5046.275694,
                "coupled_latency_us_per_token": 5046.275694,
                "ranker_fifo_capacity_ok": True,
                "ranker_required_fifo_depth_groups": 1,
                "ranker_candidate_memory_bytes": 6292,
            }
        ],
    }
    producer_physical = {
        "make_target": "3_3_place_gp",
        "boundary_kind": "physical",
        "diagnosis": {"decision": "producer_physical_boundary_not_reached"},
        "probe_rows": [
            {
                "num_modules": 16,
                "status": "ok",
                "synthesis": {
                    "elapsed_seconds": 822.8,
                    "log_tail": ["[INFO GPL-1002] Placed Cell Area            597643.1212"],
                },
                "metrics_row": {
                    "critical_path_ns": "6.104",
                    "die_area": "4840000.0",
                    "total_power_mw": "0.254",
                },
            }
        ],
    }
    producer_config = {
        "compute": {"gemm": {"mac_type": "fp16", "num_modules": 16, "lanes_per_module": 1}}
    }

    report = build_report(
        frontier=frontier,
        coupling=coupling,
        producer_physical=producer_physical,
        producer_config=producer_config,
        stream_contract_path="npu/docs/decoder_logit_rank_streaming_hierarchy.md",
    )

    assert report["producer_config_summary"]["mac_lanes_per_cycle"] == 16
    row = next(item for item in report["integration_rows"] if item["label"] == "gpt2_small")
    assert row["producer_choice"]["producer_lanes"] == 64
    assert row["nm16_mac_projection"]["measured_compute_cycles_per_tile"] == 3072
    assert row["nm16_mac_projection"]["equivalent_nm16_clusters_for_analytical_macs"] == 512
    assert row["bottleneck_if_nm16_model_clock"] == "ranker"
    assert row["bottleneck_if_nm16_physical_clock"] == "producer_mac_limited"
    assert report["recommendation"]["next_target"]["name"] == "r64_k1_nm16_ready_valid_equivalence"
    assert report["recommendation"]["next_target"]["hidden_size"] == 768
