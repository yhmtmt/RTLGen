#!/usr/bin/env python3
"""Recost finite score32 attention with global HBM service and exact Llama-2-7B MHA."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval import measure_llm_decoder_attention_score32_noc_phase2_schedule as phase2_schedule  # noqa: E402
from npu.eval.audit_llm_decoder_attention_score32_exp_lut_hbm_dram_service_closure import (  # noqa: E402
    _hbm_energy,
)
from npu.eval.audit_llm_decoder_attention_score32_hbm_controller_replay import (  # noqa: E402
    _build_burst_stream,
    _simulate_replay_cycles,
)
from npu.eval.reroute_llm_decoder_attention_score32_noc_phase2_measured_router_clock import (  # noqa: E402
    _compact_schedule,
)
from npu.eval.verify_llm_decoder_attention_score32_noc_phase2_endpoint_rtl import (  # noqa: E402
    descriptors_from_packet_specs,
    run_performance_replay,
)
from npu.eval.measure_llm_decoder_attention_score32_noc_phase2_schedule import (  # noqa: E402
    PacketSpec,
)

JsonDict = dict[str, Any]

_BASE = Path("runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1")
DEFAULT_FINITE_RECOST = _BASE / (
    "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost__"
    "l2_decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost_llama7b_v1.json"
)
DEFAULT_SOURCE_RECOST = _BASE / (
    "decoder_attention_score32_exact_reduction_recost__"
    "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json"
)
DEFAULT_HBM_REPLAY = _BASE / (
    "decoder_attention_score32_hbm_controller_replay__"
    "l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1.json"
)
DEFAULT_HBM_ENERGY = _BASE / (
    "decoder_attention_score32_exp_lut_hbm_dram_service_closure__"
    "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1.json"
)
DEFAULT_QUALITY_FRONTIER = _BASE / (
    "decoder_attention_score32_integrated_frontier_ranking__"
    "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_"
    "rtl_ppa_recost_frontier_llama7b_v1.json"
)

_FINITE_PROFILE = "decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost"
_SOURCE_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_HBM_REPLAY_MODEL = "llm_decoder_attention_score32_hbm_controller_replay_v1"
_HBM_ENERGY_MODEL = "llm_decoder_attention_score32_exp_lut_hbm_dram_service_closure_v1"
_QUALITY_FRONTIER_MODEL = "llm_decoder_attention_score32_integrated_frontier_ranking_v1"


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _positive(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{label} must be positive")
    return number


def _positive_int(value: Any, label: str) -> int:
    number = _positive(value, label)
    integer = int(number)
    if float(integer) != number:
        raise ValueError(f"{label} must be an integer")
    return integer


def _ceil_div(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("division denominator must be positive")
    return (numerator + denominator - 1) // denominator


def _validate_inputs(
    *, finite: JsonDict, source: JsonDict, hbm_replay: JsonDict, hbm_energy: JsonDict
) -> tuple[JsonDict, JsonDict, JsonDict, JsonDict]:
    if finite.get("version") != 1 or finite.get("profile") != _FINITE_PROFILE:
        raise ValueError("finite endpoint composed recost profile/version mismatch")
    model = finite.get("model_contract")
    throughput = finite.get("throughput")
    physical = finite.get("physical_recost")
    clock = finite.get("clock_contract")
    logical = finite.get("logical_schedule")
    if not all(isinstance(section, dict) for section in (model, throughput, physical, clock, logical)):
        raise ValueError("finite recost is missing required sections")
    if model.get("attention_heads") != 32 or model.get("kv_heads") != 4:
        raise ValueError("finite source must be the 32-head/4-KV-head GQA8 point")
    if model.get("gqa_group_size") != 8 or model.get("kv_sharing") != "gqa8":
        raise ValueError("finite source must expose GQA8")
    if physical.get("area_fit") is not True:
        raise ValueError("finite source must fit its die envelope")

    if source.get("version") != 1 or source.get("model") != _SOURCE_MODEL:
        raise ValueError("exact-reduction source model/version mismatch")
    best = source.get("best_requested")
    if not isinstance(best, dict):
        raise ValueError("exact-reduction source is missing best_requested")
    source_contract = {
        "hidden_size": _positive_int(best.get("hidden_size"), "hidden_size"),
        "layers": _positive_int(best.get("layers"), "layers"),
        "attention_heads": _positive_int(best.get("attention_heads"), "attention_heads"),
        "kv_heads": _positive_int(best.get("kv_heads"), "kv_heads"),
        "sequence_length": _positive_int(best.get("sequence_length"), "sequence_length"),
    }
    for key, value in source_contract.items():
        if model.get(key) != value:
            raise ValueError(f"finite/source model mismatch for {key}")
    if best.get("kv_sharing") != "gqa8":
        raise ValueError("exact-reduction source must be GQA8")

    if hbm_replay.get("version") != 1 or hbm_replay.get("model") != _HBM_REPLAY_MODEL:
        raise ValueError("HBM replay model/version mismatch")
    controller = hbm_replay.get("best_latency")
    if not isinstance(controller, dict):
        raise ValueError("HBM replay is missing best_latency")

    if hbm_energy.get("version") != 1 or hbm_energy.get("model") != _HBM_ENERGY_MODEL:
        raise ValueError("HBM energy model/version mismatch")
    energy_params = hbm_energy.get("energy_params")
    if not isinstance(energy_params, dict):
        raise ValueError("HBM energy source is missing calibrated parameters")
    for key in (
        "read_hit_pj_per_byte",
        "read_miss_pj_per_byte",
        "write_pj_per_byte",
        "activate_precharge_pj_per_row",
        "command_pj_per_burst",
    ):
        _positive(energy_params.get(key), f"HBM energy parameter {key}")
    return model, best, controller, energy_params


def _controller_ppa(quality_frontier: JsonDict) -> JsonDict:
    if quality_frontier.get("version") != 1 or quality_frontier.get("model") != _QUALITY_FRONTIER_MODEL:
        raise ValueError("quality frontier model/version mismatch")
    rows = quality_frontier.get("rows")
    if not isinstance(rows, list):
        raise ValueError("quality frontier rows are missing")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("family") == "score32_exp_lut_div"
    ]
    if len(matches) != 1:
        raise ValueError("quality frontier must contain exactly one score32 row")
    ppa = matches[0].get("score32_hbm_controller_replay_ppa")
    if not isinstance(ppa, dict):
        raise ValueError("score32 row is missing measured HBM controller PPA")
    return {
        "artifact_item_id": str(ppa.get("artifact_item_id") or ""),
        "area_mm2": _positive(ppa.get("controller_area_mm2"), "HBM controller area"),
        "power_mw": _positive(ppa.get("controller_power_mw"), "HBM controller power"),
        "critical_path_ns": _positive(
            ppa.get("critical_path_ns_best"), "HBM controller critical path"
        ),
        "metrics_csv": str(ppa.get("metrics_csv") or ""),
    }


def _projection_cycles(*, row: JsonDict, kv_heads: int) -> JsonDict:
    hidden_size = _positive_int(row.get("hidden_size"), "hidden_size")
    attention_heads = _positive_int(row.get("attention_heads"), "attention_heads")
    head_dim = hidden_size // attention_heads
    macs_per_cycle = _positive_int(
        row.get("replica_recost_macs_per_cycle", row.get("macs_per_cycle")), "macs_per_cycle"
    )
    source_kv_heads = _positive_int(row.get("kv_heads"), "source kv_heads")
    source_macs = hidden_size * hidden_size + 2 * hidden_size * source_kv_heads * head_dim
    source_cycles = _positive_int(row.get("qkv_cycles"), "source qkv_cycles")
    if _ceil_div(source_macs, macs_per_cycle) != source_cycles:
        raise ValueError("source qkv_cycles does not match the declared MAC throughput")
    target_macs = hidden_size * hidden_size + 2 * hidden_size * kv_heads * head_dim
    return {
        "source_macs": source_macs,
        "source_cycles": source_cycles,
        "target_macs": target_macs,
        "target_cycles": _ceil_div(target_macs, macs_per_cycle),
        "macs_per_cycle": macs_per_cycle,
    }


def _global_hbm_service(
    *, tile_hbm_bytes: int, active_clusters: int, controller: JsonDict, hbm_clock_ns: float
) -> JsonDict:
    aggregate_wave_bytes = tile_hbm_bytes * active_clusters
    channel_count = _positive_int(controller.get("channel_count"), "HBM channel_count")
    burst_bytes = _positive_int(controller.get("burst_bytes"), "HBM burst_bytes")
    row_span = _positive_int(controller.get("row_span_bursts"), "HBM row_span_bursts")
    row_hit_rate = _positive(controller.get("row_hit_rate"), "HBM row_hit_rate")
    channels, misses, burst_count, miss_count = _build_burst_stream(
        tile_hbm_bytes=aggregate_wave_bytes,
        burst_bytes=burst_bytes,
        channel_count=channel_count,
        row_span_bursts=row_span,
        row_hit_rate=row_hit_rate,
    )
    service_cycles = _simulate_replay_cycles(
        channel_count=channel_count,
        channel_bandwidth_bytes_per_cycle=_positive(
            controller.get("channel_bandwidth_bytes_per_cycle"), "HBM channel bandwidth"
        ),
        burst_bytes=burst_bytes,
        channels=channels,
        miss_flags=misses,
        request_overhead_cycles=int(controller.get("request_overhead_cycles", 0)),
        row_miss_penalty_cycles=int(controller.get("row_miss_penalty_cycles", 0)),
        scheduler_gap_cycles=int(controller.get("scheduler_gap_cycles", 0)),
        outstanding=_positive_int(controller.get("hbm_outstanding"), "HBM outstanding"),
        scheduler_efficiency=_positive(controller.get("scheduler_efficiency"), "HBM scheduler efficiency"),
    )
    return {
        "scope": "one_global_controller_shared_by_all_active_clusters",
        "active_clusters": active_clusters,
        "tile_hbm_bytes": tile_hbm_bytes,
        "aggregate_wave_hbm_bytes": aggregate_wave_bytes,
        "burst_count": burst_count,
        "deterministic_row_miss_count": miss_count,
        "service_cycles": service_cycles,
        "hbm_controller_clock_ns": hbm_clock_ns,
        "service_time_ns": service_cycles * hbm_clock_ns,
        "effective_global_bytes_per_second": (
            aggregate_wave_bytes / (service_cycles * hbm_clock_ns * 1.0e-9)
        ),
        "controller_parameters": {
            key: controller.get(key)
            for key in (
                "channel_count",
                "channel_bandwidth_bytes_per_cycle",
                "burst_bytes",
                "row_span_bursts",
                "row_hit_rate",
                "request_overhead_cycles",
                "row_miss_penalty_cycles",
                "hbm_outstanding",
                "scheduler_gap_cycles",
                "scheduler_efficiency",
            )
        },
    }


def _phase2_args(args: argparse.Namespace, *, noc_clock_ns: float) -> argparse.Namespace:
    return argparse.Namespace(
        repo_root=args.repo_root,
        source_json=args.source_recost_json,
        measured_l1_costs=args.measured_l1_costs,
        out=args.out,
        report=args.report,
        wave_limit=None,
        packet_payload_bytes=256,
        cluster_endpoints=None,
        root_endpoint=15,
        shared_vc=0,
        reduction_vc=1,
        compute_clock_ns=None,
        noc_clock_ns=noc_clock_ns,
        max_cycles=args.max_cycles,
    )


def _candidate(
    *,
    args: argparse.Namespace,
    candidate_id: str,
    kv_heads: int,
    exact_llama2_structure: bool,
    finite: JsonDict,
    source_row: JsonDict,
    controller: JsonDict,
    controller_ppa: JsonDict,
    energy_params: JsonDict,
    fixed_shared_tile_bytes: int,
) -> JsonDict:
    hidden_size = _positive_int(source_row.get("hidden_size"), "hidden_size")
    attention_heads = _positive_int(source_row.get("attention_heads"), "attention_heads")
    head_dim = hidden_size // attention_heads
    kv_bits = _positive_int(source_row.get("kv_bits"), "kv_bits")
    tile_tokens = _positive_int(source_row.get("tile_tokens"), "tile_tokens")
    tile_count = _positive_int(source_row.get("tile_count"), "tile_count")
    waves = _positive_int(source_row.get("tile_waves"), "tile_waves")
    active_clusters = _positive_int(source_row.get("active_clusters"), "active_clusters")
    layers = _positive_int(source_row.get("layers"), "layers")
    compute_clock_ns = _positive(
        source_row.get("measured_dual_stream_composed_clock_ns"), "compute clock"
    )
    hbm_clock_ns = _positive(source_row.get("clock_ns"), "HBM controller clock")
    full_tile_bytes = int(2 * tile_tokens * kv_heads * head_dim * kv_bits / 8)
    if fixed_shared_tile_bytes >= full_tile_bytes:
        raise ValueError("fixed shared payload must be smaller than the full KV tile")
    tile_hbm_bytes = full_tile_bytes - fixed_shared_tile_bytes
    projection = _projection_cycles(row=source_row, kv_heads=kv_heads)
    source_kv_heads = _positive_int(source_row.get("kv_heads"), "source kv_heads")
    source_kv_write_cycles = _positive_int(source_row.get("kv_write_cycles"), "kv_write_cycles")
    kv_write_cycles = _ceil_div(source_kv_write_cycles * kv_heads, source_kv_heads)
    hbm = _global_hbm_service(
        tile_hbm_bytes=tile_hbm_bytes,
        active_clusters=active_clusters,
        controller=controller,
        hbm_clock_ns=hbm_clock_ns,
    )
    arithmetic_tile_cycles = _positive_int(source_row.get("tile_attention_cycles"), "tile attention cycles")
    arithmetic_tile_time_ns = arithmetic_tile_cycles * compute_clock_ns
    wave_time_ns = max(arithmetic_tile_time_ns, float(hbm["service_time_ns"]))
    wave_compute_cycles = int(math.ceil(wave_time_ns / compute_clock_ns))
    reduction_cycles = _positive_int(source_row.get("cross_tile_reduction_cycles"), "reduction cycles")
    layer_cycles = (
        int(projection["target_cycles"])
        + waves * wave_compute_cycles
        + reduction_cycles
        + kv_write_cycles
    )

    schedule_row = dict(source_row)
    schedule_row.update(
        {
            "label": "llama2_7b_exact_mha" if exact_llama2_structure else "llama7b_gqa8_proxy",
            "kv_heads": kv_heads,
            "kv_sharing": "mha" if kv_heads == attention_heads else f"gqa{attention_heads // kv_heads}",
            "shared_byte_share": fixed_shared_tile_bytes / full_tile_bytes,
            "qkv_cycles": int(projection["target_cycles"]),
            "tile_attention_cycles": wave_compute_cycles,
            "layer_cycles": layer_cycles,
            "kv_write_cycles": kv_write_cycles,
            "kv_cache_mib": (
                2
                * _positive_int(source_row.get("sequence_length"), "sequence length")
                * kv_heads
                * head_dim
                * kv_bits
                / 8
                * layers
                / (1024 * 1024)
            ),
            "onchip_full_tile_bytes": full_tile_bytes,
            "tile_hbm_bytes": tile_hbm_bytes,
        }
    )
    packet_specs: list[PacketSpec] = []
    logical_payload = phase2_schedule.build_report(
        _phase2_args(args, noc_clock_ns=_positive(finite["clock_contract"]["effective_noc_clock_ns"], "NoC clock")),
        packet_spec_output=packet_specs,
        source_row_override=schedule_row,
        source_artifact_override=candidate_id,
    )
    logical = _compact_schedule(logical_payload)
    endpoint = run_performance_replay(
        descriptors_from_packet_specs(packet_specs), max_cycles=args.max_cycles
    )
    if endpoint["packets"] != logical["scheduled_packet_count"]:
        raise ValueError("finite endpoint replay packet count mismatch")
    if endpoint["flits"] != logical["scheduled_flit_count"]:
        raise ValueError("finite endpoint replay flit count mismatch")
    noc_clock_ns = _positive(finite["clock_contract"]["effective_noc_clock_ns"], "NoC clock")
    endpoint_time_ns = endpoint["cycles"] * noc_clock_ns
    compute_layer_time_ns = layer_cycles * compute_clock_ns
    critical_layer_time_ns = max(compute_layer_time_ns, endpoint_time_ns)
    token_time_ns = critical_layer_time_ns * layers

    service_for_energy = {
        "row_hit_rate": controller["row_hit_rate"],
        "burst_bytes": controller["burst_bytes"],
    }
    energy_row = dict(schedule_row)
    energy_row["tile_count"] = tile_count
    hbm_energy = _hbm_energy(
        tile_hbm_bytes=tile_hbm_bytes,
        service=service_for_energy,
        params=energy_params,
        source_row=energy_row,
    )
    logic_power_mw = _positive(
        finite["physical_recost"]["recost_logic_vectorless_power_mw"], "logic vectorless power"
    )
    logic_energy_mj = logic_power_mw * token_time_ns / 1.0e9
    controller_energy_mj = (
        _positive(controller_ppa.get("power_mw"), "HBM controller power")
        * token_time_ns
        / 1.0e9
    )
    logic_area_um2 = _positive(
        finite["physical_recost"]["total_embodied_area_um2"], "logic embodied area"
    )
    controller_area_um2 = (
        _positive(controller_ppa.get("area_mm2"), "HBM controller area") * 1.0e6
    )
    total_embodied_area_um2 = logic_area_um2 + controller_area_um2
    die_area_um2 = _positive(finite["physical_recost"]["die_area_um2"], "die area")
    return {
        "candidate_id": candidate_id,
        "model_contract": {
            "contract_scope": (
                "exact_llama2_7b_mha_structure"
                if exact_llama2_structure
                else "llama7b_shaped_gqa8_proxy_not_exact_llama2_7b"
            ),
            "hidden_size": hidden_size,
            "layers": layers,
            "attention_heads": attention_heads,
            "kv_heads": kv_heads,
            "gqa_group_size": attention_heads // kv_heads,
            "kv_sharing": schedule_row["kv_sharing"],
            "sequence_length": schedule_row["sequence_length"],
            "kv_bits": kv_bits,
        },
        "projection": projection,
        "memory": {
            "full_tile_bytes": full_tile_bytes,
            "fixed_shared_tile_bytes": fixed_shared_tile_bytes,
            "tile_hbm_bytes": tile_hbm_bytes,
            "kv_cache_mib": schedule_row["kv_cache_mib"],
            "kv_write_cycles_per_layer": kv_write_cycles,
            "read_bytes_per_token": hbm_energy["read_bytes_per_token"],
            "write_bytes_per_token": hbm_energy["write_bytes_per_token"],
        },
        "global_hbm_service": hbm,
        "schedule": {
            "arithmetic_tile_cycles": arithmetic_tile_cycles,
            "arithmetic_tile_time_ns": arithmetic_tile_time_ns,
            "global_hbm_wave_time_ns": hbm["service_time_ns"],
            "wave_compute_cycles": wave_compute_cycles,
            "tile_waves": waves,
            "layer_cycles": layer_cycles,
            "compute_layer_time_ns": compute_layer_time_ns,
            "finite_endpoint_drain_cycles": endpoint["cycles"],
            "finite_endpoint_drain_time_ns": endpoint_time_ns,
            "critical_layer_time_ns": critical_layer_time_ns,
            "bottleneck": "finite_endpoint_noc" if endpoint_time_ns > compute_layer_time_ns else "compute_hbm",
            "scheduled_packets": endpoint["packets"],
            "scheduled_flits": endpoint["flits"],
            "router_contention_cycles": endpoint["contention"],
        },
        "throughput": {
            "token_latency_us": token_time_ns / 1000.0,
            "token_throughput_per_s": 1.0e9 / token_time_ns,
        },
        "physical": {
            "die_area_um2": die_area_um2,
            "logic_and_onchip_memory_embodied_area_um2": logic_area_um2,
            "hbm_controller_area_um2": controller_area_um2,
            "total_embodied_area_um2": total_embodied_area_um2,
            "area_fit": total_embodied_area_um2 <= die_area_um2,
            "area_change_for_mha": "none_shared_compute_and_fixed_onchip_buffers",
            "hbm_controller_ppa": controller_ppa,
        },
        "energy": {
            "hbm_command_calibrated_energy": hbm_energy,
            "hbm_energy_mj_per_token": hbm_energy["energy_mj"],
            "logic_vectorless_energy_mj_per_token": logic_energy_mj,
            "hbm_controller_vectorless_energy_mj_per_token": controller_energy_mj,
            "total_proxy_energy_mj_per_token": (
                logic_energy_mj + controller_energy_mj + float(hbm_energy["energy_mj"])
            ),
            "logic_energy_status": "always_on_vectorless_upper_proxy_without_clock_gating",
            "hbm_energy_status": "command_calibrated_not_vendor_signoff",
        },
        "quality_contract": {
            "arithmetic_profile": finite["precision_contract"]["precision_profile"],
            "structural_model_match": exact_llama2_structure,
            "native_llama2_generation_quality_measured": False,
            "promotable": False,
            "reason": (
                "Exact MHA structure is recosted, but native Llama-2-7B score32 generation quality is not measured."
                if exact_llama2_structure
                else "GQA8 is not the exact Llama-2-7B MHA structure."
            ),
        },
    }


def build_report(args: argparse.Namespace) -> JsonDict:
    root = args.repo_root.resolve()
    finite = _load_json(root / args.finite_recost_json)
    source = _load_json(root / args.source_recost_json)
    hbm_replay = _load_json(root / args.hbm_replay_json)
    hbm_energy = _load_json(root / args.hbm_energy_json)
    quality_frontier = _load_json(root / args.quality_frontier_json)
    _model, source_row, controller, energy_params = _validate_inputs(
        finite=finite, source=source, hbm_replay=hbm_replay, hbm_energy=hbm_energy
    )
    controller_ppa = _controller_ppa(quality_frontier)
    fixed_shared_tile_bytes = _positive_int(
        source_row.get("onchip_shared_bytes_per_cluster"), "fixed shared tile bytes"
    )
    gqa8 = _candidate(
        args=args,
        candidate_id="score32_gqa8_global_hbm_finite_endpoint",
        kv_heads=4,
        exact_llama2_structure=False,
        finite=finite,
        source_row=source_row,
        controller=controller,
        controller_ppa=controller_ppa,
        energy_params=energy_params,
        fixed_shared_tile_bytes=fixed_shared_tile_bytes,
    )
    mha = _candidate(
        args=args,
        candidate_id="score32_exact_llama2_7b_mha_global_hbm_finite_endpoint",
        kv_heads=32,
        exact_llama2_structure=True,
        finite=finite,
        source_row=source_row,
        controller=controller,
        controller_ppa=controller_ppa,
        energy_params=energy_params,
        fixed_shared_tile_bytes=fixed_shared_tile_bytes,
    )
    source_throughput = _positive(finite["throughput"]["token_throughput_per_s"], "finite throughput")
    return {
        "version": 1,
        "model": "llm_decoder_attention_score32_global_hbm_exact_llama2_mha_recost_v1",
        "decision": "exact_llama2_mha_recost_recorded_native_quality_required",
        "source_items": {
            "finite_endpoint_composed_recost": (
                "l2_decoder_attention_score32_noc_phase2_finite_endpoint_composed_recost_llama7b_v1"
            ),
            "exact_reduction_recost": "l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1",
            "hbm_controller_replay": "l2_decoder_attention_score32_hbm_controller_replay_llama7b_v1",
            "hbm_energy_closure": "l2_decoder_attention_score32_exp_lut_hbm_dram_service_closure_llama7b_v1",
            "hbm_controller_ppa_frontier": (
                "l2_decoder_attention_score32_quality_aware_hbm_controller_replay_"
                "rtl_ppa_recost_frontier_llama7b_v1"
            ),
        },
        "global_controller_correction": {
            "legacy_scope": "one_tile_replayed_as_if_it_owned_the_global_controller",
            "corrected_scope": "all_active_cluster_tiles_in_one_wave_share_one_global_controller",
            "active_cluster_multiplier": source_row["active_clusters"],
            "source_finite_token_throughput_per_s": source_throughput,
            "corrected_gqa8_token_throughput_per_s": gqa8["throughput"]["token_throughput_per_s"],
            "throughput_ratio_corrected_vs_source": (
                gqa8["throughput"]["token_throughput_per_s"] / source_throughput
            ),
        },
        "rows": [gqa8, mha],
        "exact_mha_delta_vs_corrected_gqa8": {
            "qkv_projection_macs_ratio": mha["projection"]["target_macs"] / gqa8["projection"]["target_macs"],
            "kv_cache_ratio": mha["memory"]["kv_cache_mib"] / gqa8["memory"]["kv_cache_mib"],
            "read_bytes_ratio": mha["memory"]["read_bytes_per_token"] / gqa8["memory"]["read_bytes_per_token"],
            "token_latency_ratio": mha["throughput"]["token_latency_us"] / gqa8["throughput"]["token_latency_us"],
            "token_throughput_ratio": mha["throughput"]["token_throughput_per_s"] / gqa8["throughput"]["token_throughput_per_s"],
            "hbm_energy_ratio": mha["energy"]["hbm_energy_mj_per_token"] / gqa8["energy"]["hbm_energy_mj_per_token"],
        },
        "invariants": {
            "attention_qk_value_macs_unchanged": True,
            "partial_reduction_payload_unchanged": True,
            "fixed_shared_sram_bytes_unchanged": True,
            "finite_endpoint_packet_volume_unchanged": (
                gqa8["schedule"]["scheduled_packets"] == mha["schedule"]["scheduled_packets"]
                and gqa8["schedule"]["scheduled_flits"] == mha["schedule"]["scheduled_flits"]
            ),
            "compute_array_and_onchip_area_unchanged": True,
        },
        "remaining_abstractions": [
            "HBM controller service is deterministic burst replay, not controller RTL or vendor timing signoff.",
            "HBM energy is command calibrated rather than vendor current signoff.",
            "Logic energy is an always-on vectorless upper proxy; workload clock-gating activity is not measured.",
            "Native Llama-2-7B score32 generation quality has not been measured.",
            "The fixed shared-SRAM residency policy is recosted but not reoptimized for MHA.",
        ],
        "next_step": {
            "required_quality_job": "native_llama2_7b_score32_generation_quality",
            "required_architecture_job": "exact_mha_shared_sram_hbm_residency_sweep",
            "frontier_promotion_allowed": False,
        },
    }


def write_report(payload: JsonDict, path: Path) -> None:
    gqa8, mha = payload["rows"]
    lines = [
        "# Global-HBM Exact Llama-2-7B MHA Recost",
        "",
        f"- decision: `{payload['decision']}`",
        f"- corrected GQA8 throughput token/s: `{gqa8['throughput']['token_throughput_per_s']}`",
        f"- exact MHA throughput token/s: `{mha['throughput']['token_throughput_per_s']}`",
        f"- exact MHA KV cache MiB: `{mha['memory']['kv_cache_mib']}`",
        f"- exact MHA total proxy energy mJ/token: `{mha['energy']['total_proxy_energy_mj_per_token']}`",
        f"- total embodied area mm2: `{mha['physical']['total_embodied_area_um2'] / 1.0e6}`",
        "",
        "| Candidate | KV heads | QKV cycles | Wave HBM bytes | Layer cycles | Token/s | Total mJ/token | Embodied mm2 | Structural match | Promotable |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {candidate_id} | {kv_heads} | {qkv} | {wave_bytes} | {layer_cycles} | {throughput} | {energy} | {area} | {structural} | {promotable} |".format(
                candidate_id=row["candidate_id"],
                kv_heads=row["model_contract"]["kv_heads"],
                qkv=row["projection"]["target_cycles"],
                wave_bytes=row["global_hbm_service"]["aggregate_wave_hbm_bytes"],
                layer_cycles=row["schedule"]["layer_cycles"],
                throughput=row["throughput"]["token_throughput_per_s"],
                energy=row["energy"]["total_proxy_energy_mj_per_token"],
                area=row["physical"]["total_embodied_area_um2"] / 1.0e6,
                structural=row["quality_contract"]["structural_model_match"],
                promotable=row["quality_contract"]["promotable"],
            )
        )
    lines.extend(["", "## Remaining Abstractions", ""])
    lines.extend(f"- {item}" for item in payload["remaining_abstractions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--finite-recost-json", type=Path, default=DEFAULT_FINITE_RECOST)
    parser.add_argument("--source-recost-json", type=Path, default=DEFAULT_SOURCE_RECOST)
    parser.add_argument("--hbm-replay-json", type=Path, default=DEFAULT_HBM_REPLAY)
    parser.add_argument("--hbm-energy-json", type=Path, default=DEFAULT_HBM_ENERGY)
    parser.add_argument("--quality-frontier-json", type=Path, default=DEFAULT_QUALITY_FRONTIER)
    parser.add_argument("--measured-l1-costs", type=Path, default=phase2_schedule.DEFAULT_MEASURED_L1_COSTS)
    parser.add_argument("--max-cycles", type=int, default=20_000_000)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(payload, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
