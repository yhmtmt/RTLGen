from npu.eval import estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule as schedule


def _row(profile: str, latency_us: float) -> dict[str, object]:
    return {
        "measured_l1_profile": profile,
        "latency_us": latency_us,
        "topology": "mesh2d",
        "scheduler_policy": "locality_aware",
        "reduction_strategy": "cluster_tree",
        "bank_placement": "per_cluster_local",
        "cluster_count": 16,
        "bank_count": 64,
        "link_width_bits": 2048,
        "virtual_channels": 4,
        "sram_area_fraction": 0.35,
        "compute_logic_area_fraction": 0.5,
        "tile_tokens": 1024,
        "command_cycles_per_tile": 0,
        "command_cycles_per_wave": 0,
        "reducer_setup_cycles": 0,
        "reduction_cycle_multiplier": 1.0,
        "compute_replica_count": 856,
    }


def test_dedupe_rows_keeps_distinct_precision_profiles() -> None:
    payload = {
        "top_rows": [
            _row("hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8", 10.0),
            _row("hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10", 10.0),
            _row("hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12", 10.0),
        ]
    }

    rows = schedule._dedupe_rows(payload, limit=10)

    assert [row["measured_l1_profile"] for row in rows] == [
        "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q8",
        "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q10",
        "hd64_kv8_full_value_p8_ppc2_noc128_softmax_int8_q12",
    ]
