from __future__ import annotations

import argparse
import json
from pathlib import Path

from npu.eval.estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility import build_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_metrics(path: Path, *, die_area: float, power_mw: float, instance_area: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["status", "critical_path_ns", "die_area", "total_power_mw", "param_hash", "tag", "result_path"]
    if instance_area is not None:
        headers.insert(3, "instance_area_um2")
    values = {
        "status": "ok",
        "critical_path_ns": "1.0",
        "die_area": str(die_area),
        "instance_area_um2": str(instance_area if instance_area is not None else die_area),
        "total_power_mw": str(power_mw),
        "param_hash": "abc",
        "tag": "unit",
        "result_path": "results/unit",
    }
    path.write_text(",".join(headers) + "\n" + ",".join(values[key] for key in headers) + "\n", encoding="utf-8")


def _args(tmp_path: Path, *, source: Path, compute_metrics: Path | None = None) -> argparse.Namespace:
    full_value = tmp_path / "full_value.csv"
    softmax = tmp_path / "softmax.csv"
    _write_metrics(full_value, die_area=10.0, power_mw=0.1)
    _write_metrics(softmax, die_area=2.0, power_mw=0.02)
    return argparse.Namespace(
        subtile_pipeline_json=source,
        full_value_tile_metrics=full_value,
        softmax_weight_metrics=softmax,
        compute_block_metrics=compute_metrics,
        compute_block_macs_per_cycle=128 if compute_metrics else None,
        compute_arch_name="dense_gemm_int8_16x8_k1_p1" if compute_metrics else None,
        quality_gate_json=None,
        precision_profile="q8_k8_v6_a24_s24_w16_int8_compute" if compute_metrics else "q8_k8_v6_a24_s24_w16",
        model_name="unit",
        frontier_row_limit=8,
        buffer_area_um2_per_byte=0.0,
    )


def test_compute_block_substitution_can_close_dual_stream_area_gap(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_json(
        source,
        {
            "model": "unit_source",
            "best_by_compute_mode": [
                {
                    "compute_mode": "dual_mac",
                    "latency_us": 10.0,
                    "latency_speedup_vs_hbm_closed_source": 2.0,
                    "tile_service_cycles": 12,
                    "cluster_count": 1,
                    "compute_area_multiplier": 2.0,
                    "compute_area_um2": 200.0,
                    "compute_budget_um2": 250.0,
                    "measured_l1_overhead_area_um2": 20.0,
                    "local_datapath_area_um2": 5.0,
                    "softmax_weight_generator_area_um2": 1.0,
                    "logic_area_used_um2": 220.0,
                    "required_stream_buffer_bytes": 16,
                    "available_local_capacity_bytes": 32,
                    "measured_block_area_um2": 200.0,
                    "measured_block_clock_ns": 3.0,
                    "measured_block_macs_per_cycle": 128,
                    "measured_block_power_mw": 4.0,
                    "compute_replica_count": 1,
                    "compute_arch": "dense_gemm_16x8_k1_p1",
                    "macs_per_cycle": 128,
                    "clock_ns": 3.0,
                }
            ],
        },
    )
    compute_metrics = tmp_path / "int8_compute.csv"
    _write_metrics(compute_metrics, die_area=100.0, instance_area=50.0, power_mw=0.5)

    baseline = build_report(_args(tmp_path, source=source))
    substituted = build_report(_args(tmp_path, source=source, compute_metrics=compute_metrics))

    assert baseline["diagnosis"]["decision"] == "dual_stream_area_blocked"
    assert baseline["best_requested"]["compute_substitution_enabled"] is False
    assert baseline["best_requested"]["area_fit"] is False

    assert substituted["diagnosis"]["decision"] == "dual_stream_feasible"
    assert substituted["best_requested"]["compute_substitution_enabled"] is True
    assert substituted["best_requested"]["substituted_compute_arch"] == "dense_gemm_int8_16x8_k1_p1"
    assert substituted["best_requested"]["substituted_compute_replica_count"] == 1
    assert substituted["best_requested"]["substituted_compute_area_um2"] == 50.0
    assert substituted["best_requested"]["compute_area_required_um2"] == 100.0
    assert substituted["best_requested"]["area_fit"] is True
    assert substituted["best_requested"]["compute_clock_ok"] is True
