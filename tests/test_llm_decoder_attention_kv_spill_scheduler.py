from npu.eval.estimate_llm_decoder_attention_kv_capacity_noc import build_report as build_capacity_report
from npu.eval.estimate_llm_decoder_attention_kv_spill_scheduler import build_report as build_spill_report


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


def test_spill_scheduler_targets_llama_spill_point() -> None:
    report = build_spill_report(
        capacity_noc_baseline=_capacity_baseline(),
        label="llama7b_proxy",
        sequence_length=131072,
        die_area_mm2=400.0,
        tile_tokens_list=[512, 2048],
        prefetch_distance_tiles_list=[1, 8],
        hbm_outstanding_list=[1, 4],
        hbm_efficiency_list=[0.4, 0.8],
        arbitration_efficiency_list=[0.55, 0.85],
        virtual_channel_list=[1, 4],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        prefetch_start_list=["after_qkv", "during_qkv"],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    best = report["best"]
    assert best["placement"] == "shared_sram_hbm_spill"
    assert best["label"] == "llama7b_proxy"
    assert best["hbm_read_share"] > 0.0
    assert best["shared_read_share"] > 0.0


def test_spill_scheduler_improves_with_more_hbm_parallelism() -> None:
    report = build_spill_report(
        capacity_noc_baseline=_capacity_baseline(),
        label="llama7b_proxy",
        sequence_length=131072,
        die_area_mm2=400.0,
        tile_tokens_list=[1024],
        prefetch_distance_tiles_list=[8],
        hbm_outstanding_list=[1, 4],
        hbm_efficiency_list=[0.8],
        arbitration_efficiency_list=[0.85],
        virtual_channel_list=[4],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        prefetch_start_list=["during_qkv"],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    by_outstanding = {row["hbm_outstanding"]: row for row in report["top_rows"]}
    assert by_outstanding[4]["latency_us"] <= by_outstanding[1]["latency_us"]
