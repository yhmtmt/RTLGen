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
    command_dispatch_control_metrics: list[str] | None = None,
    recompute_area_fit_replicas: bool = False,
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
        command_dispatch_control_metrics=command_dispatch_control_metrics,
        compute_block_macs_per_cycle=128 if compute_metrics else None,
        compute_arch_name="dense_gemm_int8_16x8_k1_p1" if compute_metrics else None,
        quality_gate_json=None,
        precision_profile="q8_k8_v6_a24_s24_w16_int8_compute" if compute_metrics else "q8_k8_v6_a24_s24_w16",
        model_name="unit",
        frontier_row_limit=8,
        buffer_area_um2_per_byte=0.0,
        recompute_area_fit_replicas=recompute_area_fit_replicas,
        command_cycles_per_tile=None,
        command_cycles_per_wave=None,
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


def test_command_dispatch_control_metrics_are_charged_once_per_schedule(tmp_path: Path) -> None:
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
                    "cluster_count": 12,
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
    metrics_c8 = tmp_path / "attention_command_dispatch_c8_q16" / "metrics.csv"
    metrics_c16 = tmp_path / "attention_command_dispatch_c16_q32" / "metrics.csv"
    metrics_c32 = tmp_path / "attention_command_dispatch_c32_q64" / "metrics.csv"
    _write_metrics(metrics_c8, die_area=4.0, power_mw=0.04, instance_area=4.0)
    _write_metrics(metrics_c16, die_area=7.0, power_mw=0.07, instance_area=7.0)
    _write_metrics(metrics_c32, die_area=14.0, power_mw=0.14, instance_area=14.0)
    for clusters, path in [(8, metrics_c8), (16, metrics_c16), (32, metrics_c32)]:
        _write_json(
            path.parent / "config.json",
            {
                "top_name": path.parent.name,
                "attention_command_dispatch": {
                    "clusters": clusters,
                    "queue_depth": 16,
                    "tile_id_bits": 16,
                    "wave_id_bits": 12,
                    "base_token_bits": 18,
                    "max_inflight_per_cluster": 4,
                },
            },
        )

    baseline = build_report(_args(tmp_path, source=source))
    measured_control = build_report(
        _args(
            tmp_path,
            source=source,
            command_dispatch_control_metrics=[
                str(metrics_c8),
                str(metrics_c16),
                str(metrics_c32),
            ],
        )
    )

    assert baseline["best_requested"]["measured_command_dispatch_control_variant_name"] is None
    assert measured_control["inputs"]["command_dispatch_control_metrics"] == [
        str(metrics_c8),
        str(metrics_c16),
        str(metrics_c32),
    ]
    assert (
        measured_control["best_requested"]["measured_command_dispatch_control_variant_name"]
        == "attention_command_dispatch_c16_q32"
    )
    assert measured_control["best_requested"]["measured_command_dispatch_control_cluster_count"] == 16
    assert measured_control["best_requested"]["measured_command_dispatch_control_area_um2"] == 7.0
    assert measured_control["best_requested"]["command_dispatch_control_clock_ok"] is True
    assert measured_control["best_requested"]["logic_area_used_required_um2"] == (
        baseline["best_requested"]["logic_area_used_required_um2"] + 7.0
    )


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
    _write_json(
        metrics.parent / "config.json",
        {
            "top_name": "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_q12_pwl_recip_q12",
            "attention_dual_stream_composed": {
                "softmax_impl": "pwl_recip_lut",
                "semantic_profile": "q12_pwl_recip_lut",
            },
        },
    )

    result = build_report(_args(tmp_path, source=source, composed_metrics=[str(metrics)]))

    assert result["diagnosis"]["best_requested_substituted_compute_variant_label"] == "q12_pwl"
    assert result["diagnosis"]["best_requested_substituted_compute_semantic_profile"] == "q12_pwl_recip_lut"
    assert result["best_requested"]["substituted_compute_variant_label"] == "q12_pwl"
    assert result["best_requested"]["substituted_compute_semantic_profile"] == "q12_pwl_recip_lut"


def test_composed_wrapper_semantic_profile_prefers_generated_manifest(tmp_path: Path) -> None:
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
    metrics = tmp_path / "score32" / "metrics.csv"
    _write_metrics(metrics, die_area=30.0, power_mw=0.7, instance_area=28.0)
    _write_json(
        metrics.parent / "config.json",
        {
            "attention_dual_stream_composed": {
                "semantic_profile": "score32_w16_exact_div",
            },
        },
    )
    _write_json(
        metrics.parent / "verilog" / "attention_dual_stream_composed_manifest.json",
        {
            "semantic_profile": "score32_w16_recip_lut_q16",
        },
    )

    result = build_report(_args(tmp_path, source=source, composed_metrics=[str(metrics)]))

    assert (
        result["diagnosis"]["best_requested_substituted_compute_semantic_profile"]
        == "score32_w16_recip_lut_q16"
    )
    assert result["best_requested"]["measured_dual_stream_composed_semantic_profile"] == "score32_w16_recip_lut_q16"


def test_composed_wrapper_total_macs_prefers_generated_manifest_then_config(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_json(
        source,
        {
            "model": "unit_source",
            "best_by_compute_mode": [
                {
                    "compute_mode": "dual_mac",
                    "latency_us": 1.6,
                    "source_latency_us": 3.2,
                    "latency_speedup_vs_hbm_closed_source": 2.0,
                    "cluster_count": 1,
                    "compute_area_multiplier": 1.0,
                    "compute_area_um2": 180.0,
                    "compute_budget_um2": 260.0,
                    "measured_l1_overhead_area_um2": 10.0,
                    "local_datapath_area_um2": 4.0,
                    "softmax_weight_generator_area_um2": 2.0,
                    "logic_area_used_um2": 250.0,
                    "required_stream_buffer_bytes": 16,
                    "available_local_capacity_bytes": 32,
                    "measured_block_area_um2": 45.0,
                    "measured_block_clock_ns": 1.0,
                    "measured_block_macs_per_cycle": 128,
                    "measured_block_power_mw": 1.0,
                    "compute_replica_count": 2,
                    "compute_arch": "dense_gemm_16x8_k1_p1",
                    "macs_per_cycle": 256,
                    "clock_ns": 1.0,
                    "layers": 1,
                    "qkv_cycles": 10,
                    "tile_qk_cycles": 80,
                    "tile_stats_cycles": 8,
                    "tile_value_cycles": 80,
                    "tile_hbm_cycles": 10,
                    "tile_local_sram_cycles": 1,
                    "tile_shared_path_cycles": 1,
                    "tile_waves": 1,
                    "command_dispatch_cycles": 0,
                    "cross_tile_reduction_cycles": 0,
                    "kv_write_cycles": 0,
                    "subtile_count": 1,
                    "subtile_buffer_count": 1,
                    "prefetch_distance": 0,
                    "normalize_strategy": "online_correction",
                    "online_rescale_penalty_cycles": 0,
                    "subtile_stats_cycles": 8,
                    "subtile_hbm_cycles": 10,
                    "subtile_aux_memory_cycles": 1,
                    "tile_service_cycles": 88,
                }
            ],
        },
    )
    full_metrics = tmp_path / "full" / "metrics.csv"
    half_metrics = tmp_path / "half" / "metrics.csv"
    _write_metrics(full_metrics, die_area=90.0, power_mw=1.0, instance_area=90.0)
    _write_metrics(half_metrics, die_area=40.0, power_mw=0.5, instance_area=40.0)
    _write_json(
        full_metrics.parent / "verilog" / "attention_dual_stream_composed_manifest.json",
        {
            "semantic_profile": "score32_exp_lut_div",
            "total_macs": 256,
        },
    )
    _write_json(
        half_metrics.parent / "config.json",
        {
            "attention_dual_stream_composed": {
                "streams": 2,
                "array_m": 8,
                "array_n": 4,
                "k_unroll": 1,
                "semantic_profile": "score32_exp_lut_div",
            },
        },
    )

    result = build_report(
        _args(
            tmp_path,
            source=source,
            composed_metrics=[str(full_metrics), str(half_metrics)],
            recompute_area_fit_replicas=True,
        )
    )

    rows_by_name = {row["substituted_compute_arch"]: row for row in result["rows"]}
    assert rows_by_name["full"]["substituted_block_macs_per_cycle"] == 256
    assert rows_by_name["full"]["substituted_compute_replica_count"] == 1
    assert rows_by_name["half"]["substituted_block_macs_per_cycle"] == 64
    assert rows_by_name["half"]["substituted_compute_replica_count"] == 4
    assert rows_by_name["half"]["replica_recost_macs_per_cycle"] == 256


def test_composed_wrapper_can_recost_area_fit_replica_count(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    _write_json(
        source,
        {
            "model": "unit_source",
            "best_by_compute_mode": [
                {
                    "compute_mode": "dual_mac",
                    "latency_us": 1.6,
                    "source_latency_us": 3.2,
                    "latency_speedup_vs_hbm_closed_source": 2.0,
                    "cluster_count": 1,
                    "compute_area_multiplier": 1.0,
                    "compute_area_um2": 90.0,
                    "compute_budget_um2": 170.0,
                    "measured_l1_overhead_area_um2": 10.0,
                    "local_datapath_area_um2": 4.0,
                    "softmax_weight_generator_area_um2": 2.0,
                    "logic_area_used_um2": 160.0,
                    "required_stream_buffer_bytes": 16,
                    "available_local_capacity_bytes": 32,
                    "measured_block_area_um2": 45.0,
                    "measured_block_clock_ns": 1.0,
                    "measured_block_macs_per_cycle": 128,
                    "measured_block_power_mw": 1.0,
                    "compute_replica_count": 2,
                    "compute_arch": "dense_gemm_16x8_k1_p1",
                    "macs_per_cycle": 256,
                    "clock_ns": 1.0,
                    "layers": 1,
                    "qkv_cycles": 10,
                    "tile_qk_cycles": 80,
                    "tile_stats_cycles": 8,
                    "tile_value_cycles": 80,
                    "tile_hbm_cycles": 10,
                    "tile_local_sram_cycles": 1,
                    "tile_shared_path_cycles": 1,
                    "tile_waves": 1,
                    "command_dispatch_cycles": 0,
                    "cross_tile_reduction_cycles": 0,
                    "kv_write_cycles": 0,
                    "subtile_count": 1,
                    "subtile_buffer_count": 1,
                    "prefetch_distance": 0,
                    "normalize_strategy": "online_correction",
                    "online_rescale_penalty_cycles": 0,
                    "subtile_stats_cycles": 8,
                    "subtile_hbm_cycles": 10,
                    "subtile_aux_memory_cycles": 1,
                    "tile_service_cycles": 88,
                }
            ],
        },
    )
    metrics = tmp_path / "score32" / "metrics.csv"
    metrics.parent.mkdir(parents=True, exist_ok=True)
    metrics.write_text(
        "\n".join(
            [
                "status,critical_path_ns,die_area,instance_area_um2,total_power_mw,param_hash,tag,result_path",
                "ok,2.0,100.0,100.0,4.0,abc,score32,results/score32",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    blocked = build_report(_args(tmp_path, source=source, composed_metrics=[str(metrics)]))
    recost = build_report(
        _args(
            tmp_path,
            source=source,
            composed_metrics=[str(metrics)],
            recompute_area_fit_replicas=True,
        )
    )

    assert blocked["diagnosis"]["decision"] == "dual_stream_area_blocked"
    assert blocked["diagnosis"]["best_feasible_mode"] is None
    assert blocked["best_requested"]["replica_recost_enabled"] is False

    assert recost["diagnosis"]["decision"] == "dual_stream_feasible"
    assert recost["best_requested"]["replica_recost_enabled"] is True
    assert recost["best_requested"]["replica_recost_source_replica_count"] == 2
    assert recost["best_requested"]["replica_recost_area_fit_replica_count"] == 1
    assert recost["best_requested"]["replica_recost_macs_per_cycle"] == 128
    assert recost["best_requested"]["replica_recost_latency_us"] == 716.0 / 1000.0
    assert recost["best_requested"]["substituted_compute_replica_count"] == 1
    assert recost["best_requested"]["substituted_compute_area_um2"] == 100.0
    assert recost["best_requested"]["compute_area_required_um2"] == 100.0
    assert recost["best_requested"]["logic_area_slack_required_um2"] == 6.0
    assert recost["best_requested"]["compute_area_over_budget_um2"] == 0.0
    assert recost["best_requested"]["area_fit"] is True
    assert recost["best_requested"]["physical_feasible"] is True
    assert recost["best_requested"]["compute_clock_ok"] is True
    assert recost["diagnosis"]["best_feasible_latency_us"] == 716.0 / 1000.0
