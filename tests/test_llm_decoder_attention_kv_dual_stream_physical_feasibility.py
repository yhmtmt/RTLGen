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


def _args(
    tmp_path: Path,
    *,
    source: Path,
    compute_metrics: Path | None = None,
    composed_metrics: list[str] | None = None,
) -> argparse.Namespace:
    full_value = tmp_path / "full_value.csv"
    softmax = tmp_path / "softmax.csv"
    _write_metrics(full_value, die_area=10.0, power_mw=0.1)
    _write_metrics(softmax, die_area=2.0, power_mw=0.02)
    return argparse.Namespace(
        subtile_pipeline_json=source,
        full_value_tile_metrics=full_value,
        softmax_weight_metrics=softmax,
        compute_block_metrics=compute_metrics,
        composed_dual_stream_metrics=composed_metrics,
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


def test_multi_composed_wrapper_variants_use_effective_variant_clock(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_json(
        source,
        {
            "model": "unit_source",
            "best_by_compute_mode": [
                {
                    "compute_mode": "dual_mac",
                    "latency_us": 100.0,
                    "latency_speedup_vs_hbm_closed_source": 4.0,
                    "tile_service_cycles": 12,
                    "cluster_count": 1,
                    "compute_area_multiplier": 1.0,
                    "compute_area_um2": 120.0,
                    "compute_budget_um2": 1000.0,
                    "measured_l1_overhead_area_um2": 20.0,
                    "local_datapath_area_um2": 10.0,
                    "softmax_weight_generator_area_um2": 5.0,
                    "logic_area_used_um2": 150.0,
                    "required_stream_buffer_bytes": 16,
                    "available_local_capacity_bytes": 32,
                    "measured_block_area_um2": 120.0,
                    "measured_block_clock_ns": 4.0,
                    "measured_block_macs_per_cycle": 128,
                    "measured_block_power_mw": 4.0,
                    "compute_replica_count": 1,
                    "compute_arch": "dense_gemm_16x8_k1_p1",
                    "macs_per_cycle": 128,
                    "clock_ns": 4.0,
                }
            ],
        },
    )
    metrics_q8 = tmp_path / "q8.csv"
    metrics_q10 = tmp_path / "q10.csv"
    metrics_q12 = tmp_path / "q12.csv"
    _write_metrics(metrics_q8, die_area=30.0, power_mw=0.7, instance_area=28.0)
    # Override critical paths by rewriting files with explicit values.
    metrics_q8.write_text(
        "\n".join(
            [
                "status,critical_path_ns,die_area,instance_area_um2,total_power_mw,param_hash,tag,result_path",
                "ok,12.0,30.0,28.0,0.8,abc,q8,results/q8",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    metrics_q10.write_text(
        "\n".join(
            [
                "status,critical_path_ns,die_area,instance_area_um2,total_power_mw,param_hash,tag,result_path",
                "ok,4.0,28.0,26.0,0.5,abc,q10,results/q10",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    metrics_q12.write_text(
        "\n".join(
            [
                "status,critical_path_ns,die_area,instance_area_um2,total_power_mw,param_hash,tag,result_path",
                "ok,2.0,26.0,24.0,0.4,abc,q12,results/q12",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_report(
        _args(
            tmp_path,
            source=source,
            composed_metrics=[
                str(metrics_q8),
                str(metrics_q10),
                str(metrics_q12),
            ],
        )
    )

    assert len(result["rows"]) == 3
    assert result["inputs"]["composed_dual_stream_metrics"] == [str(metrics_q8), str(metrics_q10), str(metrics_q12)]
    assert (
        result["diagnosis"]["best_requested_substituted_compute_variant_label"]
        == "q12"
    )
    # source schedule latency is 100 us, so the q12 clock is 2/4 => 50 us
    assert result["diagnosis"]["best_requested_adjusted_latency_us_if_feasible"] == 50.0
    assert result["diagnosis"]["best_feasible_latency_us"] == 50.0


def test_composed_q12_pwl_wrapper_variant_label_is_concise(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_json(
        source,
        {
            "model": "unit_source",
            "best_by_compute_mode": [
                {
                    "compute_mode": "dual_mac",
                    "latency_us": 100.0,
                    "latency_speedup_vs_hbm_closed_source": 4.0,
                    "tile_service_cycles": 12,
                    "cluster_count": 1,
                    "compute_area_multiplier": 1.0,
                    "compute_area_um2": 120.0,
                    "compute_budget_um2": 1000.0,
                    "measured_l1_overhead_area_um2": 20.0,
                    "local_datapath_area_um2": 10.0,
                    "softmax_weight_generator_area_um2": 5.0,
                    "logic_area_used_um2": 150.0,
                    "required_stream_buffer_bytes": 16,
                    "available_local_capacity_bytes": 32,
                    "measured_block_area_um2": 120.0,
                    "measured_block_clock_ns": 4.0,
                    "measured_block_macs_per_cycle": 128,
                    "measured_block_power_mw": 4.0,
                    "compute_replica_count": 1,
                    "compute_arch": "dense_gemm_16x8_k1_p1",
                    "macs_per_cycle": 128,
                    "clock_ns": 4.0,
                }
            ],
        },
    )
    metrics = (
        tmp_path
        / "runs/designs/npu_blocks"
        / "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12"
        / "metrics.csv"
    )
    _write_metrics(metrics, die_area=30.0, power_mw=0.7, instance_area=28.0)

    result = build_report(_args(tmp_path, source=source, composed_metrics=[str(metrics)]))

    assert result["diagnosis"]["best_requested_substituted_compute_variant_label"] == "q12_pwl"
    assert result["best_requested"]["substituted_compute_variant_label"] == "q12_pwl"
