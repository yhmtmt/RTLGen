from npu.eval.estimate_llm_decoder_attention_kv_memory import build_report


def test_attention_kv_memory_reports_tiers_and_sharing() -> None:
    report = build_report(
        sequence_length_list=[128, 8192],
        macs_per_cycle_list=[32768],
        kv_memory_tier_list=["local_sram", "hbm"],
        kv_sharing_list=["mha", "mqa"],
        kv_bits_list=[8],
        noc_hops_list=[0, 2],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        score_bits=16,
        vector_ops_per_cycle=32768,
        weight_bandwidth_bytes_per_cycle=256.0,
        activation_bandwidth_bytes_per_cycle=512.0,
        noc_bandwidth_bytes_per_cycle=256.0,
    )

    rows = report["attention_kv_sweep"]
    assert report["model"] == "llm_decoder_attention_kv_memory_v1"
    assert {row["kv_memory_tier"] for row in rows} == {"local_sram", "hbm"}
    assert {row["kv_sharing"] for row in rows} == {"mha", "mqa"}
    assert {stage["stage"] for stage in rows[0]["stages"]} == {
        "qkv_projection",
        "kv_cache_write",
        "qk_score",
        "softmax_scores",
        "value_mix",
        "attention_output_projection",
    }


def test_attention_kv_memory_exposes_long_context_kv_pressure() -> None:
    report = build_report(
        sequence_length_list=[128, 8192],
        macs_per_cycle_list=[131072],
        kv_memory_tier_list=["local_sram", "remote_hbm"],
        kv_sharing_list=["mha"],
        kv_bits_list=[16],
        noc_hops_list=[0, 4],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        score_bits=16,
        vector_ops_per_cycle=32768,
        weight_bandwidth_bytes_per_cycle=256.0,
        activation_bandwidth_bytes_per_cycle=512.0,
        noc_bandwidth_bytes_per_cycle=128.0,
    )

    local = next(
        row
        for row in report["attention_kv_sweep"]
        if row["label"] == "llama7b_proxy"
        and row["sequence_length"] == 8192
        and row["kv_memory_tier"] == "local_sram"
        and row["weight_residency"] == "resident_weights"
    )
    remote = next(
        row
        for row in report["attention_kv_sweep"]
        if row["label"] == "llama7b_proxy"
        and row["sequence_length"] == 8192
        and row["kv_memory_tier"] == "remote_hbm"
        and row["weight_residency"] == "resident_weights"
    )

    assert remote["effective_kv_bandwidth_bytes_per_cycle"] < local["effective_kv_bandwidth_bytes_per_cycle"]
    assert remote["total_latency_us"] > local["total_latency_us"]
    assert remote["kv_read_byte_share"] > 0.5
    assert remote["dominant_substage"] in {"qk_score", "value_mix"}
