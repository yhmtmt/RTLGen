import csv
import json
from pathlib import Path

from npu.eval.audit_llm_decoder_attention_decode_score_local_cluster_frontier import build_report


def test_composed_cluster_frontier_charges_value_slices_and_retracts_prior(tmp_path: Path) -> None:
    frontier = {
        "source_schedule": {
            "hidden_size": 4096,
            "attention_heads": 32,
            "kv_heads": 4,
            "sequence_length": 131072,
            "clock_ns": 5.9811,
            "layers": 32,
            "compute_budget_um2": 400_000_000,
            "logic_area_used_um2": 399_591_889.5248,
            "compute_area_um2": 396_184_770,
            "measured_shared_sram_used_area_um2": 240_066_036.89536,
            "measured_tile_local_sram_area_um2": 39_803_772.916944,
            "command_dispatch_cycles": 0,
            "kv_write_cycles": 10,
        },
        "pareto_rows": [{"token_throughput_per_s": 669.79}],
    }
    frontier_path = tmp_path / "frontier.json"
    frontier_path.write_text(json.dumps(frontier), encoding="utf-8")
    equivalence_path = tmp_path / "equivalence.json"
    equivalence_path.write_text(
        json.dumps({"decision": "pass", "equivalence_pass": True, "score_tensor_hash": "s", "final_tensor_hash": "f"}),
        encoding="utf-8",
    )
    metrics_path = tmp_path / "metrics.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status", "critical_path_ns", "instance_area_um2"])
        writer.writeheader()
        writer.writerow({"status": "ok", "critical_path_ns": "6.4383", "instance_area_um2": "2702720"})

    report = build_report(
        prior_frontier_json=frontier_path,
        cluster_metrics_csv=metrics_path,
        equivalence_json=equivalence_path,
        cluster_counts=[32, 128, 148],
        value_response_latencies=[1, 8],
        dense_tile_area_um2=8882.54,
        dense_tile_macs_per_cycle=7.98246,
    )

    service = report["services"]["1"]
    assert service["value_slices_per_head"] == 16
    assert service["commands_per_layer"] == 512
    assert service["fill_cycles_per_block"] == 139
    assert service["replay_cycles_per_block"] == 3
    assert service["command_service_cycles"] == 2_327_010
    rows = {row["candidate_id"]: row for row in report["rows"]}
    assert rows["decode_score_local_cluster_c128_vl1"]["cluster_waves_per_layer"] == 4
    assert rows["decode_score_local_cluster_c128_vl1"]["dense_qkv_tile_count"] == 640
    assert rows["decode_score_local_cluster_c148_vl1"]["compute_budget_area_fit"] is False
    assert report["decision"].startswith("prior_decode_score_tile_frontier_retracted")
    assert report["diagnosis"]["best_no_stall_token_throughput_upper_bound_per_s"] < 1.0
    assert report["diagnosis"]["promotion_blocked"] is True
