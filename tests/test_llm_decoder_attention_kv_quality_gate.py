from npu.eval.estimate_llm_decoder_attention_kv_physical_hbm_frontier import build_report as build_physical_report
from npu.eval.estimate_llm_decoder_attention_kv_quality_gate import build_report


def _physical_frontier():
    return build_physical_report(
        label="llama7b_proxy",
        sequence_length_list=[131072],
        die_area_mm2_list=[400],
        kv_sharing_list=["mha", "gqa8", "mqa"],
        kv_bits_list=[16, 8, 4],
        stack_count_list=[1, 8],
        pseudo_channels_per_stack_list=[16],
        pseudo_channel_width_bits_list=[64],
        data_rate_mtps_list=[6400],
        hbm_efficiency_list=[0.55],
        tile_tokens_list=[1024],
        prefetch_distance_tiles_list=[4],
        hbm_outstanding_list=[8],
        arbitration_efficiency_list=[0.85],
        virtual_channel_list=[4],
        prefetch_start_list=["during_qkv"],
        sram_area_fraction=0.6,
        usable_sram_fraction=0.7,
        bitcell_area_um2_per_bit=0.02,
        local_sram_fraction=0.25,
        bank_count=16,
        bank_bandwidth_bytes_per_cycle=1024.0,
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        noc_bandwidth_bytes_per_cycle=16384.0,
        noc_hops=1,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )


def test_quality_gate_demotes_mqa_to_bound_only() -> None:
    report = build_report(
        physical_hbm_frontier=_physical_frontier(),
        sequence_length_list=[131072],
        die_area_mm2_list=[400],
    )

    assert report["recommendation"]["primary_hardware_candidate"] == "gqa8_kv8"
    assert report["recommendation"]["primary_quality_experiment"] == "gqa8_kv4"
    assert report["recommendation"]["bound_only_candidate"] == "mqa_kv4"
    assert any(row["kv_sharing"] == "mqa" for row in report["bound_only_candidates"])
    assert all(row["candidate_class"] == "bound_only_retrain_required" for row in report["bound_only_candidates"])


def test_quality_gate_keeps_gqa8_kv8_as_practical_candidate() -> None:
    report = build_report(
        physical_hbm_frontier=_physical_frontier(),
        sequence_length_list=[131072],
        die_area_mm2_list=[400],
    )

    gqa8_kv8 = next(
        row
        for row in report["practical_candidates"]
        if row["kv_sharing"] == "gqa8" and row["kv_bits"] == 8
    )
    assert gqa8_kv8["combined_quality_risk"] == "medium"
    assert gqa8_kv8["candidate_class"] == "deployable_if_model_supports_structure"
    assert gqa8_kv8["hardware_speedup_vs_mha16"] > 1.0


def test_quality_gate_marks_kv4_as_quality_experiment() -> None:
    report = build_report(
        physical_hbm_frontier=_physical_frontier(),
        sequence_length_list=[131072],
        die_area_mm2_list=[400],
    )

    assert any(
        row["kv_sharing"] == "gqa8"
        and row["kv_bits"] == 4
        and row["candidate_class"] == "quality_experiment_required"
        for row in report["quality_experiment_candidates"]
    )
