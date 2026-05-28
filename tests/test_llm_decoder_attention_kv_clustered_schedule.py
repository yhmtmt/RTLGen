from pathlib import Path

from npu.eval import estimate_llm_decoder_attention_kv_clustered_schedule as sched


def _candidate():
    return {
        "compute_arch": "nm64_flat",
        "block_macs_per_cycle": 64,
        "block_clock_ns": 2.0,
        "block_area_um2": 1000.0,
        "block_power_mw": 1.0,
        "metrics_csv": "runs/designs/npu_blocks/npu_fp16_cpp_nm64_cmp/metrics.csv",
        "metrics_tag": "unit",
        "metrics_param_hash": "unit",
    }


def _report(monkeypatch, *, strategies):
    monkeypatch.setattr(sched, "_load_compute_candidates", lambda repo_root, tag_substring: [_candidate()])
    return sched.build_report(
        repo_root=Path("."),
        tag_substring="unit",
        sequence_length_list=[2048],
        die_area_mm2_list=[1.0],
        sram_area_fraction_list=[0.4],
        logic_area_fraction_list=[0.2],
        reserved_area_fraction=0.1,
        usable_sram_fraction_list=[0.7],
        local_sram_fraction_list=[0.25],
        tile_tokens_list=[512],
        bank_count_list=[16],
        cluster_count_list=[1, 2, 4],
        noc_bandwidth_bytes_per_cycle_list=[8192.0],
        noc_hops_list=[1],
        reduction_strategy_list=strategies,
        vector_ops_per_mac=0.125,
        reduction_scalar_bytes=2,
    )


def test_clustered_schedule_exposes_tile_waves_and_reduction(monkeypatch) -> None:
    report = _report(monkeypatch, strategies=["owner_cluster"])
    by_cluster = {row["cluster_count"]: row for row in report["best_by_die_cluster"]}

    assert report["model"] == "llm_decoder_attention_kv_clustered_schedule_llama7b_v1"
    assert by_cluster[1]["tile_count"] == 4
    assert by_cluster[1]["tile_waves"] == 4
    assert by_cluster[2]["tile_waves"] == 2
    assert by_cluster[4]["tile_waves"] == 1
    assert by_cluster[2]["cross_tile_reduction_cycles"] > 0
    assert by_cluster[2]["layer_cycles"] == (
        by_cluster[2]["qkv_cycles"]
        + by_cluster[2]["tile_waves"] * by_cluster[2]["tile_service_cycles"]
        + by_cluster[2]["cross_tile_reduction_cycles"]
        + by_cluster[2]["kv_write_cycles"]
    )


def test_clustered_schedule_exposes_centralized_tile_payload(monkeypatch) -> None:
    report = _report(monkeypatch, strategies=["owner_cluster", "centralized_tile"])
    rows = {
        row["reduction_strategy"]: row
        for row in report["best_by_reduction_strategy"]
        if row["die_area_mm2"] == 1.0
    }

    assert rows["centralized_tile"]["cross_tile_reduction_payload_bytes"] > rows["owner_cluster"]["cross_tile_reduction_payload_bytes"]
    assert rows["centralized_tile"]["local_reduction_cycles"] == 0
    assert rows["owner_cluster"]["local_reduction_cycles"] > 0
    assert rows["centralized_tile"]["cross_tile_reduction_vector_cycles"] >= rows["owner_cluster"]["cross_tile_reduction_vector_cycles"]
