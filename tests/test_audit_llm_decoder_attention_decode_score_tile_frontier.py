import csv
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from npu.eval.audit_llm_decoder_attention_decode_score_tile_frontier import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_metrics(path: Path, *, area: float, delay: float, power: float, design: str) -> None:
    fields = ["status", "design", "instance_area_um2", "critical_path_ns", "total_power_mw"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "status": "ok",
                "design": design,
                "instance_area_um2": area,
                "critical_path_ns": delay,
                "total_power_mw": power,
            }
        )


def _source_schedule() -> dict:
    return {
        "latency_us": 1.0,
        "hidden_size": 16,
        "attention_heads": 2,
        "kv_heads": 1,
        "tile_tokens": 8,
        "macs_per_cycle": 16,
        "compute_replica_count": 1,
        "cluster_count": 2,
        "per_cluster_macs_per_cycle": 8,
        "measured_block_macs_per_cycle": 8,
        "compute_area_multiplier": 2,
        "compute_area_um2": 80,
        "compute_budget_um2": 200,
        "logic_area_used_um2": 100,
        "clock_ns": 5,
        "subtile_count": 2,
        "prefetch_distance": 0,
        "normalize_strategy": "online_correction",
        "compute_mode": "dual_mac",
        "qkv_cycles": 20,
        "tile_qk_cycles": 8,
        "tile_value_cycles": 8,
        "tile_stats_cycles": 4,
        "subtile_stats_cycles": 2,
        "tile_hbm_cycles": 4,
        "subtile_hbm_cycles": 2,
        "subtile_aux_memory_cycles": 1,
        "tile_local_sram_cycles": 2,
        "tile_shared_path_cycles": 2,
        "tile_waves": 2,
        "command_dispatch_cycles": 0,
        "cross_tile_reduction_cycles": 2,
        "kv_write_cycles": 1,
        "layers": 2,
    }


def _frontier_row() -> dict:
    return {
        "candidate_id": "operational_source",
        "family": "operational",
        "baseline_source_latency_us": 1.0,
        "hbm_share_scale": 1.1,
        "hbm_share_scaled_latency_us": 1.1,
        "divider_latency_us": 0.2,
        "latency_us": 1.3,
        "token_throughput_per_s": 769230.0,
        "energy_mj_per_token": 3.5,
        "logic_plus_service_area_mm2": 0.001,
        "retained_logic_area_mm2": 0.001,
        "embodied_logic_plus_score_macro_area_mm2": 0.002,
        "timing_ok": True,
        "remaining_abstractions": ["the inherited dense-int8 schedule has not yet been replayed against the separated score32 consumer"],
        "components": [
            {
                "component": "operational_dense_int8_gemm_fabric",
                "area_um2": 80,
                "critical_path_ns": 4,
                "power_mw": 2,
                "energy_mj_per_token": 0.5,
            }
        ],
    }


def test_build_report_recomputes_stage_service_and_exposes_area_throughput_pareto(tmp_path: Path) -> None:
    operational = tmp_path / "operational.json"
    schedule = tmp_path / "schedule.json"
    scalar = tmp_path / "scalar.csv"
    packed = tmp_path / "packed.csv"
    _write_json(operational, {"rows": [_frontier_row()]})
    _write_json(schedule, {"best": _source_schedule(), "top_rows": []})
    _write_metrics(scalar, area=10, delay=4, power=0.1, design="scalar_m1x8")
    _write_metrics(packed, area=12, delay=4.5, power=0.12, design="packed_m1x8")

    report = build_report(
        operational_frontier_json=operational,
        subtile_schedule_json=schedule,
        scalar_metrics_csv=scalar,
        packed_metrics_csv=packed,
    )

    assert report["model"] == "llm_decoder_attention_decode_score_tile_frontier_v1"
    assert report["diagnosis"]["energy_promotion_blocked"] is True
    assert len(report["rows"]) == 6
    by_key = {
        (row["decode_score_tile_interface"], row["decode_score_tile_deployment_policy"]): row
        for row in report["rows"]
    }
    scalar_throughput = by_key[("scalar", "throughput_matched")]
    packed_throughput = by_key[("packed", "throughput_matched")]
    assert scalar_throughput["decode_score_tile_service"]["result_cycles"] == 8
    assert packed_throughput["decode_score_tile_service"]["result_cycles"] == 1
    assert scalar_throughput["decode_score_tile_schedule"]["active_replica_count"] == 6
    assert packed_throughput["decode_score_tile_schedule"]["active_replica_count"] == 4
    assert by_key[("packed", "nominal_peak")]["decode_score_tile_schedule"]["tile_qk_cycles"] < by_key[
        ("scalar", "nominal_peak")
    ][
        "decode_score_tile_schedule"
    ]["tile_qk_cycles"]
    assert all(row["energy_mj_per_token"] == 3.5 for row in report["rows"])
    assert all(row["decode_score_tile_schedule"]["area_fit"] for row in report["pareto_rows"])
    assert all(
        "inherited dense-int8 schedule" not in " ".join(row["remaining_abstractions"]).lower()
        for row in report["rows"]
    )


def test_metric_selection_prefers_area_minimum_that_meets_schedule_clock(tmp_path: Path) -> None:
    operational = tmp_path / "operational.json"
    schedule = tmp_path / "schedule.json"
    scalar = tmp_path / "scalar.csv"
    packed = tmp_path / "packed.csv"
    _write_json(operational, {"rows": [_frontier_row()]})
    _write_json(schedule, {"best": _source_schedule(), "top_rows": []})
    fields = ["status", "design", "instance_area_um2", "critical_path_ns", "total_power_mw"]
    with scalar.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(
            [
                {"status": "ok", "design": "too_slow", "instance_area_um2": 5, "critical_path_ns": 6, "total_power_mw": 0.1},
                {"status": "ok", "design": "feasible", "instance_area_um2": 10, "critical_path_ns": 4, "total_power_mw": 0.2},
            ]
        )
    _write_metrics(packed, area=12, delay=4.5, power=0.12, design="packed")

    report = build_report(
        operational_frontier_json=operational,
        subtile_schedule_json=schedule,
        scalar_metrics_csv=scalar,
        packed_metrics_csv=packed,
    )

    assert report["selected_scalar_tile"]["design"] == "feasible"
