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
    assert "stages" not in rows[0]
    assert rows[0]["dominant_substage"] in {
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
    assert local["kv_cache_mib"] > 100.0
    assert local["kv_cache_sram_area_mm2_at_0p05um2_per_bit"] > 40.0
    assert remote["dominant_substage"] in {"qk_score", "value_mix"}


def test_attention_kv_memory_detail_rows_are_opt_in() -> None:
    compact = build_report(
        sequence_length_list=[128],
        macs_per_cycle_list=[32768],
        kv_memory_tier_list=["local_sram"],
        kv_sharing_list=["mha"],
        kv_bits_list=[8],
        noc_hops_list=[0],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        score_bits=16,
        vector_ops_per_cycle=32768,
        weight_bandwidth_bytes_per_cycle=256.0,
        activation_bandwidth_bytes_per_cycle=512.0,
        noc_bandwidth_bytes_per_cycle=256.0,
    )
    detailed = build_report(
        sequence_length_list=[128],
        macs_per_cycle_list=[32768],
        kv_memory_tier_list=["local_sram"],
        kv_sharing_list=["mha"],
        kv_bits_list=[8],
        noc_hops_list=[0],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        score_bits=16,
        vector_ops_per_cycle=32768,
        weight_bandwidth_bytes_per_cycle=256.0,
        activation_bandwidth_bytes_per_cycle=512.0,
        noc_bandwidth_bytes_per_cycle=256.0,
        include_detail=True,
    )

    assert "attention_kv_sweep_detail" not in compact
    assert "attention_kv_sweep_detail" in detailed
    assert "stages" not in compact["attention_kv_sweep"][0]
    assert "stages" in detailed["attention_kv_sweep_detail"][0]


def test_attention_kv_memory_loads_measured_tile_frontier(tmp_path) -> None:
    metrics = tmp_path / "metrics.csv"
    metrics.write_text(
        "\n".join(
            [
                "design,platform,config_hash,param_hash,tag,status,critical_path_ns,die_area,total_power_mw,params_json,result_path",
                'attention_kv_tile_hd64_kv4_l16_b128_wrapper,nangate45,cfg,slow,tag,ok,4.8,12000,0.42,"{}",result.json',
                'attention_kv_tile_hd64_kv4_l16_b128_wrapper,nangate45,cfg,fast,tag,ok,4.5,13000,0.45,"{}",result.json',
                'attention_kv_tile_hd128_kv16_l64_b512_wrapper,nangate45,cfg,wide,tag,ok,5.9,225000,2.4,"{}",result.json',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(
        sequence_length_list=[128],
        macs_per_cycle_list=[32768],
        kv_memory_tier_list=["local_sram"],
        kv_sharing_list=["mha"],
        kv_bits_list=[8],
        noc_hops_list=[0],
        clock_ns=1.0,
        weight_bits=16,
        activation_bits=16,
        score_bits=16,
        vector_ops_per_cycle=32768,
        weight_bandwidth_bytes_per_cycle=256.0,
        activation_bandwidth_bytes_per_cycle=512.0,
        noc_bandwidth_bytes_per_cycle=256.0,
        measured_tile_metrics=[str(metrics)],
    )

    frontier = report["measured_attention_kv_tile_frontier"]
    assert frontier["raw_ok_row_count"] == 3
    assert frontier["best_row_count"] == 2
    compact = frontier["best_by_design"][0]
    assert compact["design"] == "attention_kv_tile_hd64_kv4_l16_b128_wrapper"
    assert compact["param_hash"] == "fast"
    assert compact["accepted_bytes_per_tile"] == 128
    assert compact["pipeline_cycle_floor"] == 4
    assert frontier["scaling_summary"]["area_growth_largest_vs_smallest"] > 10.0
