from npu.eval.estimate_llm_decoder_attention_kv_physical_hbm_frontier import build_report


def _base_report(**overrides):
    kwargs = {
        "label": "llama7b_proxy",
        "sequence_length_list": [131072],
        "die_area_mm2_list": [100],
        "kv_sharing_list": ["gqa8"],
        "kv_bits_list": [8],
        "stack_count_list": [1],
        "pseudo_channels_per_stack_list": [16],
        "pseudo_channel_width_bits_list": [64],
        "data_rate_mtps_list": [6400],
        "hbm_efficiency_list": [0.55],
        "tile_tokens_list": [1024],
        "prefetch_distance_tiles_list": [4],
        "hbm_outstanding_list": [8],
        "arbitration_efficiency_list": [0.85],
        "virtual_channel_list": [4],
        "prefetch_start_list": ["during_qkv"],
        "sram_area_fraction": 0.6,
        "usable_sram_fraction": 0.7,
        "bitcell_area_um2_per_bit": 0.02,
        "local_sram_fraction": 0.25,
        "bank_count": 16,
        "bank_bandwidth_bytes_per_cycle": 1024.0,
        "bank_interleave_tokens": 16,
        "bank_conflict_efficiency": 0.75,
        "noc_bandwidth_bytes_per_cycle": 16384.0,
        "noc_hops": 1,
        "router_latency_cycles_per_hop": 2,
        "macs_per_cycle": 524288,
        "vector_ops_per_cycle": 65536,
        "clock_ns": 1.0,
    }
    kwargs.update(overrides)
    return build_report(**kwargs)


def test_physical_hbm_frontier_derives_bandwidth_from_phy_parameters() -> None:
    report = _base_report()
    best = report["best"]

    assert report["model"] == "llm_decoder_attention_kv_physical_hbm_frontier_llama7b_v1"
    assert best["raw_hbm_bytes_per_cycle"] == 819.2
    assert best["effective_hbm_bytes_per_cycle"] == 450.56
    assert best["dominant_tile_resource"] in {"hbm", "shared_path", "tile_attention"}


def test_physical_hbm_frontier_models_packed_kv4_reduction() -> None:
    report = _base_report(kv_bits_list=[8, 4])
    by_bits = {row["kv_bits"]: row for row in report["best_by_kv_structure"]}

    assert by_bits[4]["kv_cache_mib"] == by_bits[8]["kv_cache_mib"] / 2
    assert by_bits[4]["latency_us"] < by_bits[8]["latency_us"]
    assert by_bits[4]["hbm_byte_share"] < by_bits[8]["hbm_byte_share"]


def test_physical_hbm_frontier_improves_with_more_hbm_stacks() -> None:
    report = _base_report(stack_count_list=[1, 4], hbm_efficiency_list=[0.35])
    by_stack = {row["stack_count"]: row for row in report["best_by_hbm_physical"]}

    assert by_stack[4]["effective_hbm_bytes_per_cycle"] == 4 * by_stack[1]["effective_hbm_bytes_per_cycle"]
    assert by_stack[4]["latency_us"] < by_stack[1]["latency_us"]
