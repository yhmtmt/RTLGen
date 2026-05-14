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
