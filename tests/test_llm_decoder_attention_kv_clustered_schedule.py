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


def _report_with_overhead(monkeypatch):
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
        cluster_count_list=[2],
        noc_bandwidth_bytes_per_cycle_list=[8192.0],
        noc_hops_list=[1],
        reduction_strategy_list=["owner_cluster"],
        vector_ops_per_mac=0.125,
        reduction_scalar_bytes=2,
        command_cycles_per_tile_list=[3],
        command_cycles_per_wave_list=[5],
        reducer_setup_cycles_list=[7],
        reduction_cycle_multiplier_list=[2.0],
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


def test_clustered_schedule_charges_command_and_reducer_overhead(monkeypatch) -> None:
    report = _report_with_overhead(monkeypatch)
    row = report["best"]

    assert row["command_dispatch_cycles"] == row["tile_count"] * 3 + row["tile_waves"] * 5
    assert row["cross_tile_reduction_cycles"] == row["base_cross_tile_reduction_cycles"] * 2 + 7
    assert row["layer_cycles"] == (
        row["qkv_cycles"]
        + row["tile_waves"] * row["tile_service_cycles"]
        + row["command_dispatch_cycles"]
        + row["cross_tile_reduction_cycles"]
        + row["kv_write_cycles"]
    )
    assert report["inputs"]["command_cycles_per_tile_list"] == [3]
    assert report["inputs"]["reduction_cycle_multiplier_list"] == [2.0]


def test_clustered_schedule_charges_measured_l1_profile(monkeypatch) -> None:
    monkeypatch.setattr(sched, "_load_compute_candidates", lambda repo_root, tag_substring: [_candidate()])
    report = sched.build_report(
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
        cluster_count_list=[2],
        noc_bandwidth_bytes_per_cycle_list=[8192.0],
        noc_hops_list=[1],
        reduction_strategy_list=["owner_cluster"],
        vector_ops_per_mac=0.125,
        reduction_scalar_bytes=2,
        measured_l1_profiles=[
            {
                "name": "unit_l1",
                "fifo_per_cluster": 1,
                "router_per_cluster": 2,
                "local_datapath": {
                    "clock_ns": 3.0,
                    "area_um2": 10000.0,
                    "power_mw": 0.5,
                    "metrics_csv": "local.csv",
                },
                "noc_fifo": {
                    "clock_ns": 1.0,
                    "area_um2": 1000.0,
                    "power_mw": 0.1,
                    "metrics_csv": "fifo.csv",
                },
                "noc_router": {
                    "clock_ns": 0.5,
                    "area_um2": 500.0,
                    "power_mw": 0.05,
                    "metrics_csv": "router.csv",
                },
            }
        ],
    )
    row = report["best"]

    assert row["measured_l1_profile"] == "unit_l1"
    assert row["measured_l1_overhead_area_um2"] == 24000.0
    assert row["measured_l1_overhead_power_mw"] == 1.4
    assert row["clock_ns"] == 3.0
    assert row["compute_replica_count"] == 176
    assert row["logic_area_used_um2"] == 200000.0
    assert row["local_datapath_metrics_csv"] == "local.csv"
    assert report["best_by_measured_l1_profile"][0]["measured_l1_profile"] == "unit_l1"
