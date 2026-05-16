from npu.eval.estimate_llm_decoder_attention_kv_capacity_noc import build_report as build_capacity_report
from npu.eval.estimate_llm_decoder_attention_kv_hbm_controller import build_report as build_hbm_report


def _capacity_baseline() -> dict:
    return build_capacity_report(
        sequence_length_list=[131072],
        kv_sharing_list=["mqa"],
        kv_bits_list=[8],
        die_area_mm2_list=[400],
        sram_area_fraction_list=[0.6],
        usable_sram_fraction_list=[0.7],
        bitcell_area_um2_per_bit_list=[0.05],
        local_sram_fraction_list=[0.25],
        bank_count_list=[16],
        bank_bandwidth_bytes_per_cycle_list=[1024],
        noc_bandwidth_bytes_per_cycle_list=[16384],
        noc_hops_list=[1],
        hbm_bandwidth_bytes_per_cycle_list=[4096],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )


def test_hbm_controller_targets_llama_spill_point() -> None:
    report = build_hbm_report(
        capacity_noc_baseline=_capacity_baseline(),
        label="llama7b_proxy",
        sequence_length=131072,
        die_area_mm2=400.0,
        tile_tokens_list=[1024],
        prefetch_distance_tiles_list=[2],
        channel_count_list=[4],
        channel_bandwidth_bytes_per_cycle_list=[256],
        burst_bytes_list=[512],
        hbm_outstanding_list=[2],
        request_overhead_cycles_list=[8],
        row_hit_rate_list=[0.75],
        row_miss_penalty_cycles_list=[32],
        scheduler_efficiency_list=[0.75],
        arbitration_efficiency_list=[0.85],
        virtual_channel_list=[4],
        prefetch_start_list=["during_qkv"],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    best = report["best"]
    assert best["placement"] == "shared_sram_hbm_spill"
    assert best["label"] == "llama7b_proxy"
    assert best["derived_hbm_efficiency"] > 0.0
    assert best["service_cycles"] >= best["payload_cycles"]


def test_hbm_controller_improves_with_more_channels() -> None:
    report = build_hbm_report(
        capacity_noc_baseline=_capacity_baseline(),
        label="llama7b_proxy",
        sequence_length=131072,
        die_area_mm2=400.0,
        tile_tokens_list=[2048],
        prefetch_distance_tiles_list=[2],
        channel_count_list=[4, 16],
        channel_bandwidth_bytes_per_cycle_list=[256],
        burst_bytes_list=[1024],
        hbm_outstanding_list=[4],
        request_overhead_cycles_list=[4],
        row_hit_rate_list=[0.9],
        row_miss_penalty_cycles_list=[16],
        scheduler_efficiency_list=[0.9],
        arbitration_efficiency_list=[0.85],
        virtual_channel_list=[4],
        prefetch_start_list=["during_qkv"],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    by_channels = {row["channel_count"]: row for row in report["top_rows"]}
    assert by_channels[16]["derived_hbm_efficiency"] >= by_channels[4]["derived_hbm_efficiency"]
    assert by_channels[16]["latency_us"] <= by_channels[4]["latency_us"]
