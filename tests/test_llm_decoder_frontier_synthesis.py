from npu.eval.synthesize_llm_decoder_frontier import build_report


def test_frontier_synthesis_carries_producer_physical_boundary() -> None:
    stage_breakdown = {
        "model": "stage_model",
        "breakdown_sweep": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "hidden_size": 768,
                "vocab_size": 50257,
                "macs_per_cycle": 32768,
                "memory_bandwidth_bytes_per_cycle": 256,
                "weight_residency": "resident_weights",
                "stage_shares": {"mlp": 0.2, "norm_residual": 0.01},
                "total_latency_us": 100.0,
            }
        ],
    }
    attention_kv = {
        "model": "attention_model",
        "focus_summary": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "total_latency_us": 25.0,
                "kv_memory_tier": "shared_sram",
                "kv_sharing": "gqa4",
                "kv_bits": 8,
                "noc_hops": 1,
                "dominant_substage": "kv_read",
                "kv_limited_cycle_share": 0.5,
            }
        ],
        "measured_attention_kv_tile_frontier": {"scaling_summary": {"best": "tile"}},
    }
    physical_boundary = {
        "decision": "producer_physical_boundary_not_reached",
        "num_modules": 16,
        "critical_path_ns": 6.104,
    }
    producer_ranker = {
        "model": "producer_ranker_model",
        "producer_physical_boundary": physical_boundary,
        "coupled_ranker_sweep": [
            {
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "top_k": 1,
                "memory_share": 1.0,
                "producer_ii_cycles": 24,
                "service_limiter": "weight_memory",
                "ranker_traffic_reduction_vs_materialized": 0.99,
                "ranker_fifo_capacity_ok": True,
                "coupled_latency_us_per_token": 10.0,
            }
        ],
    }

    report = build_report(
        stage_breakdown=stage_breakdown,
        attention_kv=attention_kv,
        producer_ranker=producer_ranker,
    )

    assert report["inputs"]["producer_physical_boundary"] == physical_boundary
    assert "feasibility/PPA context" in report["assumptions"][3]


def test_frontier_synthesis_carries_producer_ranker_integration_accounting() -> None:
    stage_breakdown = {
        "model": "stage_model",
        "breakdown_sweep": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "hidden_size": 768,
                "vocab_size": 50257,
                "macs_per_cycle": 32768,
                "memory_bandwidth_bytes_per_cycle": 256,
                "weight_residency": "resident_weights",
                "stage_shares": {"mlp": 0.2, "norm_residual": 0.01},
                "total_latency_us": 100.0,
            }
        ],
    }
    attention_kv = {
        "model": "attention_model",
        "focus_summary": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "total_latency_us": 25.0,
                "kv_memory_tier": "shared_sram",
                "kv_sharing": "gqa4",
                "kv_bits": 8,
                "noc_hops": 1,
                "dominant_substage": "kv_read",
                "kv_limited_cycle_share": 0.5,
            }
        ],
        "measured_attention_kv_tile_frontier": {"scaling_summary": {"best": "tile"}},
    }
    producer_ranker = {
        "model": "producer_ranker_model",
        "coupled_ranker_sweep": [
            {
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "top_k": 1,
                "memory_share": 1.0,
                "producer_ii_cycles": 24,
                "service_limiter": "weight_memory",
                "ranker_traffic_reduction_vs_materialized": 0.99,
                "ranker_fifo_capacity_ok": True,
                "coupled_latency_us_per_token": 10.0,
            }
        ],
    }
    integration = {
        "model": "decoder_output_projection_producer_ranker_integration_v1",
        "decision": {"decision": "producer_output_ranker_integration_accounting_passed"},
        "summary": {
            "ok_integrations": 1,
            "total_integrations": 1,
            "max_ranker_area_over_producer": 0.12,
            "max_ranker_power_over_producer": 0.14,
        },
        "integrations": [
            {
                "arch_id": "fp16_nm2",
                "macro_mode": "flat_nomacro",
                "producer_lanes": 128,
                "integrated_accounting": {
                    "timing_bottleneck": "producer",
                    "critical_path_ns_max": 5.7,
                },
            }
        ],
    }

    report = build_report(
        stage_breakdown=stage_breakdown,
        attention_kv=attention_kv,
        producer_ranker=producer_ranker,
        producer_ranker_integration=integration,
    )

    accounting = report["inputs"]["producer_ranker_integration_accounting"]
    assert accounting["decision"] == "producer_output_ranker_integration_accounting_passed"
    assert accounting["max_ranker_area_over_producer"] == 0.12
    assert accounting["timing_bottlenecks"][0]["timing_bottleneck"] == "producer"
    assert "measured additive PPA context" in report["assumptions"][4]


def test_frontier_synthesis_uses_policy_calibrated_producer_latency() -> None:
    stage_breakdown = {
        "model": "stage_model",
        "breakdown_sweep": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "hidden_size": 768,
                "vocab_size": 50257,
                "macs_per_cycle": 32768,
                "memory_bandwidth_bytes_per_cycle": 256,
                "weight_residency": "resident_weights",
                "stage_shares": {"mlp": 0.2, "norm_residual": 0.01},
                "total_latency_us": 100.0,
            }
        ],
    }
    attention_kv = {
        "model": "attention_model",
        "focus_summary": [
            {
                "label": "gpt2_small",
                "sequence_length": 128,
                "total_latency_us": 25.0,
                "kv_memory_tier": "shared_sram",
                "kv_sharing": "gqa4",
                "kv_bits": 8,
                "noc_hops": 1,
                "dominant_substage": "kv_read",
                "kv_limited_cycle_share": 0.5,
            }
        ],
        "measured_attention_kv_tile_frontier": {"scaling_summary": {"best": "tile"}},
    }
    producer_ranker = {
        "model": "producer_ranker_model",
        "coupled_ranker_sweep": [
            {
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 64,
                "top_k": 1,
                "memory_share": 1.0,
                "producer_ii_cycles": 384,
                "service_limiter": "ranker",
                "ranker_fifo_capacity_ok": True,
                "coupled_latency_us_per_token": 1000.0,
            }
        ],
    }
    calibration = {
        "model": "decoder_output_projection_producer_ranker_policy_calibration_v1",
        "decision": {"decision": "producer_ranker_policy_calibration_completed"},
        "summary": {
            "row_count": 1,
            "calibrated_row_count": 1,
            "missing_wrapper_physical_rows": 0,
            "producer_dominant_rows": 1,
            "ranker_dominant_rows": 0,
            "old_to_calibrated_best_latency_speedup": 100.0,
        },
        "old_best": {"coupled_latency_us_per_token": 1000.0},
        "calibrated_best": {
            "calibrated_coupled_latency_us_per_token": 10.0,
            "calibrated_dominant_term": "producer",
        },
        "calibrated_coupled_ranker_sweep": [
            {
                "status": "ok",
                "hidden_size": 768,
                "vocab_size": 50257,
                "producer_lanes": 128,
                "top_k": 1,
                "memory_share": 1.0,
                "producer_ii_cycles": 768,
                "service_limiter": "weight_memory",
                "ranker_fifo_capacity_ok": True,
                "calibrated_coupled_latency_us_per_token": 10.0,
                "calibrated_ranker_latency_us_per_token": 0.2,
                "calibrated_selected_path": "threshold_serial_lpc1",
                "old_coupled_latency_us_per_token": 1000.0,
            }
        ],
    }

    report = build_report(
        stage_breakdown=stage_breakdown,
        attention_kv=attention_kv,
        producer_ranker=producer_ranker,
        producer_ranker_policy_calibration=calibration,
    )

    row = report["focus_summary"][0]
    assert report["model"] == "llm_decoder_frontier_synthesis_policy_calibrated_v1"
    assert row["dominant_component"] == "attention_kv_best"
    assert row["component_latency_us"]["output_projection_producer_ranker"] == 10.0
    assert row["producer_choice"]["calibrated_selected_path"] == "threshold_serial_lpc1"
    assert report["inputs"]["producer_ranker_policy_calibration"]["producer_dominant_rows"] == 1
