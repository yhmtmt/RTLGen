from npu.eval.estimate_llm_decoder_attention_kv_capacity_noc import build_report as build_capacity_report
from npu.eval.estimate_llm_decoder_attention_kv_noc_scheduler import build_report as build_scheduler_report


def _capacity_baseline() -> dict:
    return build_capacity_report(
        sequence_length_list=[131072],
        kv_sharing_list=["mqa"],
        kv_bits_list=[8],
        die_area_mm2_list=[100, 200],
        sram_area_fraction_list=[0.6],
        usable_sram_fraction_list=[0.7],
        bitcell_area_um2_per_bit_list=[0.02],
        local_sram_fraction_list=[0.75],
        bank_count_list=[64],
        bank_bandwidth_bytes_per_cycle_list=[1024],
        noc_bandwidth_bytes_per_cycle_list=[4096],
        noc_hops_list=[4],
        hbm_bandwidth_bytes_per_cycle_list=[1024],
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )


def test_scheduler_preserves_capacity_frontier_selected_points() -> None:
    report = build_scheduler_report(
        capacity_noc_baseline=_capacity_baseline(),
        selected_points=[("gpt2_small", 131072, 100.0), ("gpt2_small", 131072, 200.0)],
        tile_tokens_list=[256, 2048],
        virtual_channel_list=[1, 4],
        arbitration_efficiency_list=[0.55, 0.85],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    rows = {row["die_area_mm2"]: row for row in report["best_by_point"]}
    assert rows[100.0]["placement"] != "local_sram"
    assert rows[200.0]["placement"] == "local_sram"
    assert rows[200.0]["overlap_latency_us"] < rows[100.0]["overlap_latency_us"]


def test_scheduler_reports_strict_and_overlap_bounds() -> None:
    report = build_scheduler_report(
        capacity_noc_baseline=_capacity_baseline(),
        selected_points=[("gpt2_small", 131072, 100.0)],
        tile_tokens_list=[128, 2048],
        virtual_channel_list=[1],
        arbitration_efficiency_list=[0.55],
        bank_interleave_tokens=16,
        bank_conflict_efficiency=0.75,
        router_latency_cycles_per_hop=2,
        macs_per_cycle=524288,
        vector_ops_per_cycle=65536,
        clock_ns=1.0,
    )

    row = report["best_by_point"][0]
    assert row["strict_latency_us"] >= row["overlap_latency_us"]
    assert row["overlap_gain"] >= 1.0
    by_tile = {row["tile_tokens"]: row for row in report["all_rows"]}
    assert by_tile[2048]["noc_cycles_per_layer"] <= by_tile[128]["noc_cycles_per_layer"]
