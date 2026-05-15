from npu.eval.estimate_llm_decoder_attention_kv_capacity_noc import build_report


def test_capacity_noc_disallows_local_when_kv_cache_does_not_fit() -> None:
    report = build_report(
        sequence_length_list=[131072],
        kv_sharing_list=["mqa"],
        kv_bits_list=[8],
        die_area_mm2_list=[25],
        sram_area_fraction_list=[0.2],
        usable_sram_fraction_list=[0.55],
        bitcell_area_um2_per_bit_list=[0.1],
        local_sram_fraction_list=[0.5],
        bank_count_list=[16],
        bank_bandwidth_bytes_per_cycle_list=[64],
        noc_bandwidth_bytes_per_cycle_list=[1024],
        noc_hops_list=[4],
        hbm_bandwidth_bytes_per_cycle_list=[256],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    small = next(
        row
        for row in report["best_by_die"]
        if row["label"] == "gpt2_small" and row["sequence_length"] == 131072
    )
    assert small["kv_cache_mib"] == 192.0
    assert small["local_capacity_mib"] < small["kv_cache_mib"]
    assert small["placement"] != "local_sram"
    assert small["limiter"] in {"hbm_bw", "noc_bw", "shared_bank_bw"}


def test_capacity_noc_moves_to_local_when_die_budget_is_large() -> None:
    report = build_report(
        sequence_length_list=[131072],
        kv_sharing_list=["mqa"],
        kv_bits_list=[8],
        die_area_mm2_list=[25, 400],
        sram_area_fraction_list=[0.6],
        usable_sram_fraction_list=[0.7],
        bitcell_area_um2_per_bit_list=[0.02],
        local_sram_fraction_list=[0.75],
        bank_count_list=[256],
        bank_bandwidth_bytes_per_cycle_list=[1024],
        noc_bandwidth_bytes_per_cycle_list=[4096],
        noc_hops_list=[2],
        hbm_bandwidth_bytes_per_cycle_list=[1024],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    rows = {
        row["die_area_mm2"]: row
        for row in report["best_by_die"]
        if row["label"] == "gpt2_medium_proxy" and row["sequence_length"] == 131072
    }
    assert rows[25.0]["placement"] != "local_sram"
    assert rows[400.0]["placement"] == "local_sram"
    assert rows[400.0]["total_latency_us"] < rows[25.0]["total_latency_us"]
