#!/usr/bin/env python3
"""Check physical feasibility of the dual-stream sub-tile attention schedule."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

JsonDict = dict[str, Any]


def _effective_latency_us(row: JsonDict) -> float:
    value = row.get("adjusted_latency_us_if_feasible")
    if value is None:
        value = row.get("replica_recost_latency_us")
    if value is None:
        value = row.get("latency_us")
    return float(value)


def _load_json(path: Path) -> JsonDict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_ok_metrics(path: Path) -> JsonDict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise RuntimeError(f"no status=ok metrics rows in {path}")
    best = min(
        rows,
        key=lambda row: (
            float(row.get("critical_path_ns") or "inf"),
            float(row.get("die_area") or "inf"),
            float(row.get("total_power_mw") or "inf"),
        ),
    )
    return {
        "metrics_csv": str(path),
        "critical_path_ns": float(best["critical_path_ns"]),
        "die_area_um2": float(best["die_area"]),
        "total_power_mw": float(best["total_power_mw"]),
        "param_hash": best.get("param_hash", ""),
        "tag": best.get("tag", ""),
        "result_path": best.get("result_path", ""),
    }


def _best_ok_compute_metrics(path: Path) -> JsonDict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "ok"]
    if not rows:
        raise RuntimeError(f"no status=ok compute metrics rows in {path}")
    best = min(
        rows,
        key=lambda row: (
            float(row.get("critical_path_ns") or "inf"),
            float(row.get("instance_area_um2") or row.get("die_area") or "inf"),
            float(row.get("total_power_mw") or "inf"),
        ),
    )
    block_area = float(best.get("instance_area_um2") or best["die_area"])
    return {
        "metrics_csv": str(path),
        "critical_path_ns": float(best["critical_path_ns"]),
        "block_area_um2": block_area,
        "die_area_um2": float(best["die_area"]),
        "total_power_mw": float(best["total_power_mw"]),
        "param_hash": best.get("param_hash", ""),
        "tag": best.get("tag", ""),
        "result_path": best.get("result_path", ""),
    }


def _infer_composed_precision_profile(path: Path) -> str:
    path_text = str(path)
    if "softmax_q12_pwl_recip_q12" in path_text:
        return "q12_pwl"
    match = re.search(r"softmax_recip_lut_(q\d+)", path_text)
    if match:
        return match.group(1)
    if path.stem and path.stem != "metrics":
        return path.stem
    return path.parent.name or path.stem


def _compose_variant_name(path: Path) -> str:
    return path.parent.name


def _load_composed_semantic_profile(path: Path) -> str:
    design_dir = path.parent
    manifest_path = design_dir / "verilog" / "attention_dual_stream_composed_manifest.json"
    schedule_manifest_path = design_dir / "verilog" / "attention_dual_stream_schedule_wrapper_manifest.json"
    config_path = design_dir / "config.json"
    for candidate in (manifest_path, schedule_manifest_path, config_path):
        if not candidate.exists():
            continue
        try:
            payload = _load_json(candidate)
        except json.JSONDecodeError:
            continue
        if candidate == manifest_path:
            profile = payload.get("semantic_profile")
        elif candidate == schedule_manifest_path:
            datapath = payload.get("datapath_manifest")
            profile = datapath.get("semantic_profile") if isinstance(datapath, dict) else None
        else:
            comp = payload.get("attention_dual_stream_composed")
            if not isinstance(comp, dict):
                wrapper = payload.get("attention_dual_stream_schedule_wrapper")
                datapath = wrapper.get("datapath") if isinstance(wrapper, dict) else None
                comp = datapath if isinstance(datapath, dict) else None
            profile = comp.get("semantic_profile") if isinstance(comp, dict) else None
        if isinstance(profile, str) and profile.strip():
            return profile.strip()
    return "fixed_point"


def _load_composed_total_macs(path: Path) -> int | None:
    design_dir = path.parent
    manifest_path = design_dir / "verilog" / "attention_dual_stream_composed_manifest.json"
    schedule_manifest_path = design_dir / "verilog" / "attention_dual_stream_schedule_wrapper_manifest.json"
    config_path = design_dir / "config.json"
    if manifest_path.exists():
        try:
            manifest = _load_json(manifest_path)
        except json.JSONDecodeError:
            manifest = {}
        try:
            total_macs = int(manifest.get("total_macs"))
        except (TypeError, ValueError):
            total_macs = 0
        if total_macs > 0:
            return total_macs
    if schedule_manifest_path.exists():
        try:
            manifest = _load_json(schedule_manifest_path)
        except json.JSONDecodeError:
            manifest = {}
        try:
            total_macs = int(manifest.get("total_macs"))
        except (TypeError, ValueError):
            total_macs = 0
        if total_macs > 0:
            return total_macs
    if config_path.exists():
        try:
            payload = _load_json(config_path)
        except json.JSONDecodeError:
            payload = {}
        comp = payload.get("attention_dual_stream_composed") if isinstance(payload, dict) else None
        if not isinstance(comp, dict):
            wrapper = payload.get("attention_dual_stream_schedule_wrapper") if isinstance(payload, dict) else None
            if isinstance(wrapper, dict):
                datapath = wrapper.get("datapath")
                clusters = int(wrapper.get("clusters", 1))
                comp = datapath if isinstance(datapath, dict) else None
            else:
                clusters = 1
        else:
            clusters = 1
        if isinstance(comp, dict):
            try:
                streams = int(comp.get("streams", 2))
                array_m = int(comp.get("array_m", 16))
                array_n = int(comp.get("array_n", 8))
                k_unroll = int(comp.get("k_unroll", 1))
            except (TypeError, ValueError):
                return None
            total_macs = clusters * streams * array_m * array_n * k_unroll
            if total_macs > 0:
                return total_macs
    return None


def _load_composed_variant_kind(path: Path) -> str:
    design_dir = path.parent
    if (design_dir / "verilog" / "attention_dual_stream_schedule_wrapper_manifest.json").exists():
        return "dual_stream_schedule_wrapper"
    if (design_dir / "verilog" / "attention_dual_stream_composed_manifest.json").exists():
        return "dual_stream_composed_datapath"
    config_path = design_dir / "config.json"
    if config_path.exists():
        try:
            payload = _load_json(config_path)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload.get("attention_dual_stream_schedule_wrapper"), dict):
            return "dual_stream_schedule_wrapper"
        if isinstance(payload.get("attention_dual_stream_composed"), dict):
            return "dual_stream_composed_datapath"
    return "unknown_composed_compute_block"


def _parse_composed_metric_inputs(values: Any) -> list[Path]:
    if not values:
        return []
    raw_values = values
    if isinstance(raw_values, (str, Path)):
        raw_values = [raw_values]
    elif not isinstance(raw_values, (list, tuple)):
        raise TypeError(f"invalid composed metric input: {type(raw_values)!r}")
    paths: list[Path] = []
    for value in raw_values:
        value_text = str(value)
        for piece in value_text.split(","):
            piece = piece.strip()
            if not piece:
                continue
            paths.append(Path(piece))
    if not paths:
        return []
    return paths


def _int_override_list(text: str | None) -> list[int | None]:
    if text is None or not str(text).strip():
        return [None]
    values: list[int | None] = []
    for piece in str(text).split(","):
        piece = piece.strip()
        if not piece:
            continue
        value = int(piece)
        if value < 0:
            raise argparse.ArgumentTypeError("command cycle overrides must be non-negative")
        values.append(value)
    return values or [None]


def _load_composed_variants(paths: list[Path]) -> list[JsonDict]:
    variants: list[JsonDict] = []
    for path in paths:
        metrics = _best_ok_compute_metrics(path)
        total_macs = _load_composed_total_macs(path)
        metrics.update(
            {
                "composed_variant_label": _infer_composed_precision_profile(path),
                "composed_variant_name": _compose_variant_name(path),
                "composed_variant_kind": _load_composed_variant_kind(path),
                "composed_semantic_profile": _load_composed_semantic_profile(path),
                "composed_total_macs_per_cycle": total_macs,
            }
        )
        variants.append(metrics)
    return variants


def _infer_command_dispatch_clusters(path: Path) -> int | None:
    config_path = path.parent / "config.json"
    if config_path.exists():
        try:
            payload = _load_json(config_path)
        except json.JSONDecodeError:
            payload = {}
        ctrl = payload.get("attention_command_dispatch") if isinstance(payload, dict) else None
        if isinstance(ctrl, dict):
            try:
                clusters = int(ctrl.get("clusters"))
            except (TypeError, ValueError):
                clusters = 0
            if clusters > 0:
                return clusters
    match = re.search(r"(?:^|_)c(\d+)(?:_|$)", path.parent.name)
    if match:
        return int(match.group(1))
    return None


def _load_command_dispatch_control_variants(paths: list[Path]) -> list[JsonDict]:
    variants: list[JsonDict] = []
    for path in paths:
        metrics = _best_ok_compute_metrics(path)
        clusters = _infer_command_dispatch_clusters(path)
        if clusters is None:
            raise RuntimeError(
                "could not infer command-dispatch cluster count from metrics path; "
                f"add a sibling config.json with attention_command_dispatch.clusters: {path}"
            )
        metrics.update(
            {
                "command_dispatch_control_cluster_count": clusters,
                "command_dispatch_control_variant_name": path.parent.name,
            }
        )
        variants.append(metrics)
    variants.sort(
        key=lambda row: (
            int(row["command_dispatch_control_cluster_count"]),
            float(row["block_area_um2"]),
            float(row["critical_path_ns"]),
        )
    )
    return variants


def _select_command_dispatch_control_variant(
    variants: list[JsonDict],
    *,
    clusters: int,
) -> JsonDict | None:
    if not variants:
        return None
    covering = [
        row
        for row in variants
        if int(row["command_dispatch_control_cluster_count"]) >= clusters
    ]
    if covering:
        return min(
            covering,
            key=lambda row: (
                int(row["command_dispatch_control_cluster_count"]),
                float(row["block_area_um2"]),
                float(row["critical_path_ns"]),
            ),
        )
    return max(
        variants,
        key=lambda row: (
            int(row["command_dispatch_control_cluster_count"]),
            -float(row["block_area_um2"]),
            -float(row["critical_path_ns"]),
        ),
    )


def _with_command_overhead(source_row: JsonDict, *, per_tile: int | None, per_wave: int | None) -> JsonDict:
    if per_tile is None and per_wave is None:
        return dict(source_row)
    row = dict(source_row)
    command_cycles_per_tile = int(row.get("command_cycles_per_tile", 0)) if per_tile is None else int(per_tile)
    command_cycles_per_wave = int(row.get("command_cycles_per_wave", 0)) if per_wave is None else int(per_wave)
    command_dispatch_cycles = int(row["tile_count"]) * command_cycles_per_tile + int(row["tile_waves"]) * command_cycles_per_wave
    row.update(
        {
            "command_cycles_per_tile": command_cycles_per_tile,
            "command_cycles_per_wave": command_cycles_per_wave,
            "command_dispatch_cycles": command_dispatch_cycles,
            "command_overhead_override_enabled": True,
            "command_overhead_variant": f"ct{command_cycles_per_tile}_cw{command_cycles_per_wave}",
        }
    )
    row.update(_scheduled_subtile_pipeline(row))
    return row


def _source_rows(payload: JsonDict, *, limit: int) -> list[JsonDict]:
    rows = list(payload.get("best_by_compute_mode") or [])
    if isinstance(payload.get("best"), dict):
        rows.insert(0, payload["best"])
    deduped: list[JsonDict] = []
    seen: set[str] = set()
    for row in rows:
        key = json.dumps(
            {
                "compute_mode": row.get("compute_mode"),
                "latency_us": row.get("latency_us"),
                "tile_service_cycles": row.get("tile_service_cycles"),
                "subtile_count": row.get("subtile_count"),
                "subtile_buffer_count": row.get("subtile_buffer_count"),
                "prefetch_distance": row.get("prefetch_distance"),
                "normalize_strategy": row.get("normalize_strategy"),
            },
            sort_keys=True,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
        if len(deduped) >= limit:
            break
    return deduped


def _row_with_budget(
    source_row: JsonDict,
    *,
    full_value_tile: JsonDict,
    softmax_weight: JsonDict,
    composed_dual_stream: JsonDict | None,
    compute_block: JsonDict | None,
    command_dispatch_control: JsonDict | None,
    compute_block_macs_per_cycle: int | None,
    compute_arch_name: str | None,
    buffer_area_um2_per_byte: float,
    precision_profile: str,
    recompute_area_fit_replicas: bool,
) -> JsonDict:
    clusters = int(source_row["cluster_count"])
    compute_multiplier = float(source_row.get("compute_area_multiplier", 1.0))
    current_compute_area = float(source_row["compute_area_um2"])
    compute_budget = float(source_row["compute_budget_um2"])
    current_l1_overhead = float(source_row["measured_l1_overhead_area_um2"])
    current_local_datapath_area = float(source_row["local_datapath_area_um2"])
    current_softmax_area = float(source_row["softmax_weight_generator_area_um2"])
    current_logic_used = float(source_row["logic_area_used_um2"])
    required_buffer_bytes = int(source_row.get("required_stream_buffer_bytes", source_row.get("tile_local_buffer_bytes", 0)))
    available_local_capacity = int(source_row.get("available_local_capacity_bytes", source_row.get("local_capacity_bytes_per_cluster", 0)))
    control_area = float(command_dispatch_control["block_area_um2"]) if command_dispatch_control else 0.0
    control_clock_ns = float(command_dispatch_control["critical_path_ns"]) if command_dispatch_control else 0.0
    control_power_mw = float(command_dispatch_control["total_power_mw"]) if command_dispatch_control else 0.0

    measured_stream_area = float(full_value_tile["die_area_um2"])
    measured_softmax_area = float(softmax_weight["die_area_um2"])
    source_clock_ns = float(source_row["clock_ns"])
    use_composed_dual_stream = composed_dual_stream is not None
    if use_composed_dual_stream:
        composed_area = float(composed_dual_stream.get("block_area_um2") or composed_dual_stream["die_area_um2"])
        composed_clock_ns = float(composed_dual_stream["critical_path_ns"])
        composed_power = float(composed_dual_stream["total_power_mw"])
        source_block_macs_per_cycle = int(
            composed_dual_stream.get("composed_total_macs_per_cycle")
            or source_row["measured_block_macs_per_cycle"]
        )
        composed_replica_count = int(
            math.ceil(float(source_row["macs_per_cycle"]) / max(1, source_block_macs_per_cycle))
        )
    else:
        composed_area = 0.0
        composed_clock_ns = 0.0
        composed_power = 0.0
        composed_replica_count = 0
    stream_buffer_area = required_buffer_bytes * buffer_area_um2_per_byte

    if use_composed_dual_stream:
        # The composed wrapper contains both int8 streams, reciprocal-LUT softmax, and stream-buffer/control.
        # Replace local+softmax+compute through a single measured area term.
        selected_local_datapath_area = 0.0
        selected_softmax_area = 0.0
        selected_l1_overhead = current_l1_overhead + clusters * (
            stream_buffer_area - current_local_datapath_area - current_softmax_area
        )
    else:
        selected_local_datapath_area = compute_multiplier * measured_stream_area
        selected_softmax_area = measured_softmax_area
        selected_l1_overhead = current_l1_overhead + clusters * (
            selected_local_datapath_area
            + selected_softmax_area
            + stream_buffer_area
            - current_local_datapath_area
            - current_softmax_area
        )

    compute_substitution_enabled = use_composed_dual_stream or (compute_block is not None)
    if use_composed_dual_stream:
        target_block_area = composed_area
        target_replica_count = composed_replica_count
        target_block_macs = source_block_macs_per_cycle
        base_compute_area = target_replica_count * target_block_area
        base_compute_power = target_replica_count * composed_power
        target_block_clock = composed_clock_ns
        target_block_power = composed_power
        target_arch = str(
            composed_dual_stream.get("composed_variant_name")
            or "attention_dual_stream_composed_int8_q8k8v6_16x8_p8_ppc2_nohash_softmax_recip_lut_q10"
        )
        composed_variant_kind = str(composed_dual_stream.get("composed_variant_kind") or "dual_stream_composed_datapath")
        compute_area_required = base_compute_area
    elif compute_block is None:
        base_compute_area = current_compute_area
        base_compute_power = float(source_row.get("compute_power_mw", source_row.get("measured_block_power_mw", 0.0)))
        target_replica_count = int(source_row["compute_replica_count"])
        target_block_area = float(source_row["measured_block_area_um2"])
        target_block_macs = int(source_row["measured_block_macs_per_cycle"])
        target_block_clock = float(source_row["measured_block_clock_ns"])
        target_block_power = float(source_row.get("measured_block_power_mw", 0.0))
        target_arch = str(source_row.get("compute_arch", ""))
        composed_variant_kind = None
        compute_area_required = base_compute_area * compute_multiplier
    else:
        target_block_area = float(compute_block["block_area_um2"])
        target_block_macs = int(compute_block_macs_per_cycle or source_row["measured_block_macs_per_cycle"])
        target_replica_count = int(math.ceil(float(source_row["macs_per_cycle"]) / max(1, target_block_macs)))
        base_compute_area = target_replica_count * target_block_area
        target_block_clock = float(compute_block["critical_path_ns"])
        target_block_power = float(compute_block["total_power_mw"])
        base_compute_power = target_replica_count * target_block_power
        target_arch = str(compute_arch_name or source_row.get("compute_arch", ""))
        composed_variant_kind = None
        compute_area_required = base_compute_area * compute_multiplier
    logic_used_required = current_logic_used + (compute_area_required - current_compute_area) + (
        selected_l1_overhead - current_l1_overhead
    ) + control_area
    logic_slack_required = compute_budget - logic_used_required
    compute_area_over_budget = max(0.0, logic_used_required - compute_budget)
    required_compute_density_gain = (
        compute_area_required / max(1.0, compute_budget - selected_l1_overhead)
    )
    if compute_block is None and not use_composed_dual_stream:
        replica_count_budgeted = int(current_compute_area // max(1.0, target_block_area))
    else:
        replica_count_budgeted = int(max(0.0, compute_budget - selected_l1_overhead) // max(1.0, target_block_area))
    replica_count_required = int(
        math.ceil(target_replica_count * (compute_multiplier if not use_composed_dual_stream else 1.0))
    )
    replica_shortfall = max(0, replica_count_required - replica_count_budgeted)
    area_fit = logic_slack_required >= 0.0
    buffer_fit = required_buffer_bytes <= available_local_capacity
    command_dispatch_control_clock_ok = (
        command_dispatch_control is None or control_clock_ns <= float(source_row["clock_ns"])
    )
    feasible = area_fit and buffer_fit and command_dispatch_control_clock_ok

    if feasible:
        if use_composed_dual_stream and composed_clock_ns > 0.0 and source_clock_ns > 0.0:
            adjusted_latency_us = float(source_row["latency_us"]) * composed_clock_ns / source_clock_ns
            adjusted_speedup = float(source_row["latency_speedup_vs_hbm_closed_source"]) * source_clock_ns / composed_clock_ns
        else:
            adjusted_latency_us = float(source_row["latency_us"])
            adjusted_speedup = float(source_row["latency_speedup_vs_hbm_closed_source"])
        adjusted_tile_service_cycles = int(source_row["tile_service_cycles"])
    else:
        adjusted_latency_us = None
        adjusted_tile_service_cycles = None
        adjusted_speedup = None
        if compute_multiplier > 1.0:
            # If the doubled stream cannot fit, the nearest already-measured same-area schedule is split_mac.
            adjusted_latency_us = None

    out = dict(source_row)
    out.update(
        {
            "dual_stream_physical_model": (
                "measured_dual_stream_schedule_wrapper_budget_v1"
                if use_composed_dual_stream and composed_variant_kind == "dual_stream_schedule_wrapper"
                else "measured_dual_stream_composed_budget_v1"
                if use_composed_dual_stream
                else "measured_full_value_tile_budget_v1"
            ),
            "precision_profile": precision_profile,
            "measured_full_value_tile_metrics_csv": full_value_tile["metrics_csv"],
            "measured_full_value_tile_area_um2": measured_stream_area,
            "measured_full_value_tile_clock_ns": full_value_tile["critical_path_ns"],
            "measured_full_value_tile_power_mw": full_value_tile["total_power_mw"],
            "measured_softmax_weight_metrics_csv": softmax_weight["metrics_csv"],
            "measured_softmax_weight_area_um2": measured_softmax_area,
            "measured_softmax_weight_clock_ns": softmax_weight["critical_path_ns"],
            "measured_softmax_weight_power_mw": softmax_weight["total_power_mw"],
            **(
                {
                    "measured_dual_stream_composed_metrics_csv": composed_dual_stream["metrics_csv"],
                    "measured_dual_stream_composed_area_um2": composed_area,
                    "measured_dual_stream_composed_clock_ns": composed_clock_ns,
                    "measured_dual_stream_composed_power_mw": composed_power,
                    "measured_dual_stream_composed_required_replicas": composed_replica_count,
                    "measured_dual_stream_composed_precision_profile": composed_dual_stream[
                        "composed_variant_label"
                    ],
                    "measured_dual_stream_composed_variant_kind": composed_variant_kind,
                    "measured_dual_stream_composed_semantic_profile": composed_dual_stream[
                        "composed_semantic_profile"
                    ],
                }
                if use_composed_dual_stream
                else {}
            ),
            "stream_buffer_area_um2_per_byte": buffer_area_um2_per_byte,
            "stream_buffer_area_um2_per_cluster": round(stream_buffer_area, 6),
            "selected_local_datapath_area_um2_per_cluster": round(selected_local_datapath_area, 6),
            "selected_l1_overhead_area_um2": round(selected_l1_overhead, 6),
            "compute_area_required_um2": round(compute_area_required, 6),
            "measured_command_dispatch_control_metrics_csv": (
                command_dispatch_control["metrics_csv"] if command_dispatch_control else None
            ),
            "measured_command_dispatch_control_variant_name": (
                command_dispatch_control["command_dispatch_control_variant_name"]
                if command_dispatch_control
                else None
            ),
            "measured_command_dispatch_control_cluster_count": (
                command_dispatch_control["command_dispatch_control_cluster_count"]
                if command_dispatch_control
                else None
            ),
            "measured_command_dispatch_control_area_um2": (
                round(control_area, 6) if command_dispatch_control else None
            ),
            "measured_command_dispatch_control_clock_ns": (
                round(control_clock_ns, 6) if command_dispatch_control else None
            ),
            "measured_command_dispatch_control_power_mw": (
                round(control_power_mw, 6) if command_dispatch_control else None
            ),
            "compute_area_multiplier_required": compute_multiplier,
            "compute_substitution_enabled": compute_substitution_enabled,
            "source_compute_arch": source_row.get("compute_arch"),
            "substituted_compute_arch": target_arch if compute_substitution_enabled else None,
            "substituted_compute_metrics_csv": (
                composed_dual_stream["metrics_csv"]
                if use_composed_dual_stream
                else compute_block["metrics_csv"] if compute_block else None
            ),
            "substituted_block_area_um2": round(target_block_area, 6) if compute_substitution_enabled else None,
            "substituted_block_clock_ns": round(target_block_clock, 6) if compute_substitution_enabled else None,
            "substituted_block_power_mw": round(target_block_power, 6) if compute_substitution_enabled else None,
            "substituted_block_macs_per_cycle": target_block_macs if compute_substitution_enabled else None,
            "substituted_compute_replica_count": target_replica_count if compute_substitution_enabled else None,
            "substituted_compute_area_um2": round(base_compute_area, 6) if compute_substitution_enabled else None,
            "substituted_compute_power_mw": round(base_compute_power, 6) if compute_substitution_enabled else None,
            "substituted_compute_plus_control_power_mw": (
                round(base_compute_power + control_power_mw, 6) if compute_substitution_enabled else None
            ),
            "substituted_compute_variant_label": (
                composed_dual_stream["composed_variant_label"] if use_composed_dual_stream else None
            ),
            "substituted_compute_semantic_profile": (
                composed_dual_stream["composed_semantic_profile"] if use_composed_dual_stream else None
            ),
            "substituted_compute_variant_kind": composed_variant_kind if use_composed_dual_stream else None,
            "logic_area_used_required_um2": round(logic_used_required, 6),
            "logic_area_slack_required_um2": round(logic_slack_required, 6),
            "compute_area_over_budget_um2": round(compute_area_over_budget, 6),
            "required_compute_density_gain": round(required_compute_density_gain, 6),
            "replica_count_required": replica_count_required,
            "replica_count_budgeted_at_current_compute_area": replica_count_budgeted,
            "replica_count_shortfall": replica_shortfall,
            "local_datapath_clock_ok": float(full_value_tile["critical_path_ns"]) <= float(source_row["clock_ns"]),
            "softmax_weight_clock_ok": float(softmax_weight["critical_path_ns"]) <= float(source_row["clock_ns"]),
            "compute_clock_ok": target_block_clock <= float(source_row["clock_ns"]),
            "command_dispatch_control_clock_ok": command_dispatch_control_clock_ok,
            "area_fit": area_fit,
            "buffer_fit": buffer_fit,
            "physical_feasible": feasible,
            "adjusted_latency_us_if_feasible": adjusted_latency_us,
            "adjusted_tile_service_cycles_if_feasible": adjusted_tile_service_cycles,
            "adjusted_speedup_if_feasible": adjusted_speedup,
            "replica_recost_enabled": False,
            "replica_recost_source_replica_count": None,
            "replica_recost_area_fit_replica_count": None,
            "replica_recost_macs_per_cycle": None,
            "replica_recost_latency_us": None,
            "replica_recost_tile_service_cycles": None,
            "replica_recost_layer_cycles": None,
            "replica_recost_total_cycles": None,
        }
    )
    if recompute_area_fit_replicas and compute_substitution_enabled and replica_count_budgeted > 0:
        recost = _area_fit_replica_recost(
            source_row,
            target_replica_count=target_replica_count,
            area_fit_replica_count=min(target_replica_count, replica_count_budgeted),
            block_macs_per_cycle=target_block_macs,
            block_clock_ns=target_block_clock,
            block_power_mw=target_block_power,
            target_block_area_um2=target_block_area,
            source_block_macs_per_cycle=int(source_row["measured_block_macs_per_cycle"]),
            source_clock_ns=float(source_row["clock_ns"]),
            current_compute_area_um2=current_compute_area,
            compute_budget_um2=compute_budget,
            logic_area_used_um2=current_logic_used,
            selected_l1_overhead_area_um2=selected_l1_overhead,
            current_l1_overhead_area_um2=current_l1_overhead,
            command_dispatch_control_area_um2=control_area,
            command_dispatch_control_power_mw=control_power_mw,
            command_dispatch_control_clock_ok=command_dispatch_control_clock_ok,
            buffer_fit=buffer_fit,
        )
        out.update(recost)
    return out


def _ceil_scaled_cycles(value: Any, *, old_macs: int, new_macs: int) -> int:
    return int(math.ceil(float(value) * max(1, old_macs) / max(1, new_macs)))


def _area_fit_replica_recost(
    source_row: JsonDict,
    *,
    target_replica_count: int,
    area_fit_replica_count: int,
    block_macs_per_cycle: int,
    block_clock_ns: float,
    block_power_mw: float,
    target_block_area_um2: float,
    source_block_macs_per_cycle: int,
    source_clock_ns: float,
    current_compute_area_um2: float,
    compute_budget_um2: float,
    logic_area_used_um2: float,
    selected_l1_overhead_area_um2: float,
    current_l1_overhead_area_um2: float,
    command_dispatch_control_area_um2: float,
    command_dispatch_control_power_mw: float,
    command_dispatch_control_clock_ok: bool,
    buffer_fit: bool,
) -> JsonDict:
    new_macs = max(1, int(area_fit_replica_count) * max(1, int(block_macs_per_cycle)))
    old_macs = max(1, int(source_row.get("macs_per_cycle", target_replica_count * source_block_macs_per_cycle)))
    qkv_cycles = _ceil_scaled_cycles(source_row["qkv_cycles"], old_macs=old_macs, new_macs=new_macs)
    tile_qk_cycles = _ceil_scaled_cycles(source_row["tile_qk_cycles"], old_macs=old_macs, new_macs=new_macs)
    tile_value_cycles = _ceil_scaled_cycles(source_row["tile_value_cycles"], old_macs=old_macs, new_macs=new_macs)
    source_scaled = dict(source_row)
    source_scaled.update(
        {
            "qkv_cycles": qkv_cycles,
            "tile_qk_cycles": tile_qk_cycles,
            "tile_value_cycles": tile_value_cycles,
            "clock_ns": block_clock_ns,
        }
    )
    scheduled = _scheduled_subtile_pipeline(source_scaled)
    compute_area = int(area_fit_replica_count) * target_block_area_um2
    compute_power = int(area_fit_replica_count) * block_power_mw
    logic_required = logic_area_used_um2 + (compute_area - current_compute_area_um2) + (
        selected_l1_overhead_area_um2 - current_l1_overhead_area_um2
    ) + command_dispatch_control_area_um2
    logic_slack = compute_budget_um2 - logic_required
    compute_over_budget = max(0.0, logic_required - compute_budget_um2)
    density_gain = compute_area / max(1.0, compute_budget_um2 - selected_l1_overhead_area_um2)
    area_fit = logic_required <= compute_budget_um2
    recost_feasible = area_fit and buffer_fit and command_dispatch_control_clock_ok
    source_latency_us = float(source_row["latency_us"])
    latency_us = float(scheduled["latency_us"])
    return {
        "replica_recost_enabled": True,
        "replica_recost_source_replica_count": target_replica_count,
        "replica_recost_area_fit_replica_count": int(area_fit_replica_count),
        "replica_recost_macs_per_cycle": new_macs,
        "replica_recost_clock_ns": round(block_clock_ns, 6),
        "replica_recost_qkv_cycles": qkv_cycles,
        "replica_recost_tile_qk_cycles": tile_qk_cycles,
        "replica_recost_tile_value_cycles": tile_value_cycles,
        "replica_recost_tile_service_cycles": scheduled["tile_service_cycles"],
        "replica_recost_layer_cycles": scheduled["layer_cycles"],
        "replica_recost_total_cycles": scheduled["total_cycles"],
        "replica_recost_latency_us": latency_us,
        "replica_recost_latency_slowdown_vs_source": round(latency_us / max(1e-9, source_latency_us), 6),
        "replica_recost_compute_area_um2": round(compute_area, 6),
        "replica_recost_compute_power_mw": round(compute_power, 6),
        "replica_recost_logic_area_required_um2": round(logic_required, 6),
        "replica_recost_logic_area_slack_um2": round(logic_slack, 6),
        "replica_recost_area_fit": area_fit,
        "replica_recost_buffer_fit": buffer_fit,
        "replica_recost_physical_feasible": recost_feasible,
        "replica_recost_compute_clock_ok": True,
        "replica_recost_command_dispatch_control_clock_ok": command_dispatch_control_clock_ok,
        "substituted_compute_replica_count": int(area_fit_replica_count),
        "substituted_compute_area_um2": round(compute_area, 6),
        "substituted_compute_power_mw": round(compute_power, 6),
        "substituted_compute_plus_control_power_mw": round(
            compute_power + command_dispatch_control_power_mw,
            6,
        ),
        "compute_area_required_um2": round(compute_area, 6),
        "logic_area_used_required_um2": round(logic_required, 6),
        "logic_area_slack_required_um2": round(logic_slack, 6),
        "compute_area_over_budget_um2": round(compute_over_budget, 6),
        "required_compute_density_gain": round(density_gain, 6),
        "replica_count_required": int(area_fit_replica_count),
        "replica_count_shortfall": 0 if area_fit else max(0, target_replica_count - area_fit_replica_count),
        "compute_clock_ok": True if recost_feasible else block_clock_ns <= source_clock_ns,
        "command_dispatch_control_clock_ok": command_dispatch_control_clock_ok,
        "area_fit": True if recost_feasible else area_fit,
        "physical_feasible": recost_feasible,
        "adjusted_latency_us_if_feasible": latency_us if recost_feasible else None,
        "adjusted_tile_service_cycles_if_feasible": scheduled["tile_service_cycles"] if recost_feasible else None,
        "adjusted_speedup_if_feasible": (
            float(source_row["source_latency_us"]) / latency_us
            if recost_feasible and source_row.get("source_latency_us") is not None
            else None
        ),
    }


def _scheduled_subtile_pipeline(row: JsonDict) -> JsonDict:
    subtiles = int(row.get("subtile_count", 1))
    prefetch_distance = int(row.get("prefetch_distance", 0))
    normalize_strategy = str(row.get("normalize_strategy", "online_correction"))
    compute_mode = str(row.get("compute_mode", "dual_mac"))
    qk_sub, value_sub = _compute_stage_cycles(row, subtiles=subtiles, compute_mode=compute_mode)
    stats_sub = int(row.get("subtile_stats_cycles", math.ceil(int(row["tile_stats_cycles"]) / subtiles)))
    hbm_sub = int(row.get("subtile_hbm_cycles", math.ceil(int(row["tile_hbm_cycles"]) / subtiles)))
    memory_aux_sub = int(
        row.get(
            "subtile_aux_memory_cycles",
            max(
                math.ceil(int(row.get("tile_local_sram_cycles", 0)) / subtiles),
                math.ceil(int(row.get("tile_shared_path_cycles", 0)) / subtiles),
            ),
        )
    )
    hbm_end = [max(0, index + 1 - prefetch_distance) * hbm_sub for index in range(subtiles)]
    stats_end: list[int] = []
    value_end: list[int] = []
    shared_gemm_free = 0
    qk_free = 0
    value_free = 0
    stats_free = 0

    for index in range(subtiles):
        qk_start = max(qk_free, hbm_end[index], index * memory_aux_sub)
        if compute_mode == "shared_mac":
            qk_start = max(qk_start, shared_gemm_free)
        qk_done = qk_start + qk_sub
        qk_free = qk_done
        if compute_mode == "shared_mac":
            shared_gemm_free = qk_done

        stats_start = max(stats_free, qk_done)
        stats_done = stats_start + stats_sub
        stats_end.append(stats_done)
        stats_free = stats_done

        if normalize_strategy == "full_tile_normalize":
            continue
        value_start = max(value_free, stats_done + int(row.get("online_rescale_penalty_cycles", 0)), hbm_end[index])
        if compute_mode == "shared_mac":
            value_start = max(value_start, shared_gemm_free)
        value_done = value_start + value_sub
        value_end.append(value_done)
        value_free = value_done
        if compute_mode == "shared_mac":
            shared_gemm_free = value_done

    if normalize_strategy == "full_tile_normalize":
        all_stats_done = stats_end[-1]
        for index in range(subtiles):
            value_start = max(value_free, all_stats_done, hbm_end[index])
            if compute_mode == "shared_mac":
                value_start = max(value_start, shared_gemm_free)
            value_done = value_start + value_sub
            value_end.append(value_done)
            value_free = value_done
            if compute_mode == "shared_mac":
                shared_gemm_free = value_done
    elif normalize_strategy != "online_correction":
        raise ValueError(f"unknown normalize strategy: {normalize_strategy}")

    hbm_exposed_cycles = hbm_end[-1]
    pipeline_cycles = max(value_end[-1], hbm_exposed_cycles, subtiles * memory_aux_sub)
    residual_memory_cycles = max(int(row.get("tile_local_sram_cycles", 0)), int(row.get("tile_shared_path_cycles", 0)))
    tile_service_cycles = max(pipeline_cycles, residual_memory_cycles)
    layer_cycles = (
        int(row["qkv_cycles"])
        + int(row["tile_waves"]) * tile_service_cycles
        + int(row.get("command_dispatch_cycles", 0))
        + int(row["cross_tile_reduction_cycles"])
        + int(row["kv_write_cycles"])
    )
    total_cycles = layer_cycles * int(row["layers"])
    return {
        "subtile_qk_cycles": qk_sub,
        "subtile_value_cycles": value_sub,
        "tile_service_cycles": tile_service_cycles,
        "layer_cycles": layer_cycles,
        "total_cycles": total_cycles,
        "latency_us": round(total_cycles * float(row["clock_ns"]) / 1000.0, 6),
    }


def _compute_stage_cycles(row: JsonDict, *, subtiles: int, compute_mode: str) -> tuple[int, int]:
    qk_base = int(row["tile_qk_cycles"])
    value_base = int(row["tile_value_cycles"])
    if compute_mode == "shared_mac":
        scale = 1.0
    elif compute_mode == "split_mac":
        scale = 2.0
    elif compute_mode == "dual_mac":
        scale = 1.0
    else:
        raise ValueError(f"unknown compute mode: {compute_mode}")
    return int(math.ceil(qk_base * scale / subtiles)), int(math.ceil(value_base * scale / subtiles))


def _effective_selection_key(row: JsonDict) -> tuple[float, float, float, str]:
    substituted_area = row.get("substituted_compute_area_um2")
    substituted_power = row.get("substituted_compute_plus_control_power_mw")
    if substituted_power is None:
        substituted_power = row.get("substituted_compute_power_mw")
    if substituted_area is None:
        substituted_area = row.get("compute_area_required_um2")
    if substituted_area is None:
        substituted_area = float("inf")
    if substituted_power is None:
        substituted_power = float("inf")
    return (
        _effective_latency_us(row),
        float(substituted_area),
        float(substituted_power),
        str(row.get("compute_mode", "")),
    )


def build_report(args: argparse.Namespace) -> JsonDict:
    source = _load_json(args.subtile_pipeline_json)
    source_rows = _source_rows(source, limit=args.frontier_row_limit)
    command_cycles_per_tile_overrides = _int_override_list(args.command_cycles_per_tile)
    command_cycles_per_wave_overrides = _int_override_list(args.command_cycles_per_wave)
    full_value_tile = _best_ok_metrics(args.full_value_tile_metrics)
    softmax_weight = _best_ok_metrics(args.softmax_weight_metrics)
    composed_dual_stream_metrics = _parse_composed_metric_inputs(getattr(args, "composed_dual_stream_metrics", None))
    composed_variants = _load_composed_variants(composed_dual_stream_metrics) if composed_dual_stream_metrics else []
    command_dispatch_control_metrics = _parse_composed_metric_inputs(
        getattr(args, "command_dispatch_control_metrics", None)
    )
    command_dispatch_control_variants = (
        _load_command_dispatch_control_variants(command_dispatch_control_metrics)
        if command_dispatch_control_metrics
        else []
    )
    compute_block = _best_ok_compute_metrics(args.compute_block_metrics) if args.compute_block_metrics else None
    quality_gate = _load_json(args.quality_gate_json) if args.quality_gate_json else None
    rows: list[JsonDict] = []
    for source_row in source_rows:
        overhead_rows = [
            _with_command_overhead(source_row, per_tile=per_tile, per_wave=per_wave)
            for per_tile in command_cycles_per_tile_overrides
            for per_wave in command_cycles_per_wave_overrides
        ]
        for row in overhead_rows:
            command_dispatch_control = _select_command_dispatch_control_variant(
                command_dispatch_control_variants,
                clusters=int(row["cluster_count"]),
            )
            if composed_variants:
                for composed_dual_stream in composed_variants:
                    rows.append(
                        _row_with_budget(
                            row,
                            full_value_tile=full_value_tile,
                            softmax_weight=softmax_weight,
                            composed_dual_stream=composed_dual_stream,
                            compute_block=compute_block,
                            command_dispatch_control=command_dispatch_control,
                            compute_block_macs_per_cycle=args.compute_block_macs_per_cycle,
                            compute_arch_name=args.compute_arch_name,
                            buffer_area_um2_per_byte=args.buffer_area_um2_per_byte,
                            precision_profile=args.precision_profile,
                            recompute_area_fit_replicas=args.recompute_area_fit_replicas,
                        )
                    )
            else:
                rows.append(
                    _row_with_budget(
                        row,
                        full_value_tile=full_value_tile,
                        softmax_weight=softmax_weight,
                        composed_dual_stream=None,
                        compute_block=compute_block,
                        command_dispatch_control=command_dispatch_control,
                        compute_block_macs_per_cycle=args.compute_block_macs_per_cycle,
                        compute_arch_name=args.compute_arch_name,
                        buffer_area_um2_per_byte=args.buffer_area_um2_per_byte,
                        precision_profile=args.precision_profile,
                        recompute_area_fit_replicas=args.recompute_area_fit_replicas,
                    )
                )
    feasible_rows = [row for row in rows if row["physical_feasible"]]
    best_requested = min(rows, key=_effective_selection_key) if rows else None
    best_feasible = min(feasible_rows, key=_effective_selection_key) if feasible_rows else None
    best_area_fit = min(
        (row for row in rows if row["area_fit"]),
        key=_effective_selection_key,
        default=None,
    )
    decision = "dual_stream_feasible" if best_feasible and best_feasible.get("compute_mode") == "dual_mac" else "dual_stream_area_blocked"
    assumptions = [
        "The dual_mac schedule requires an explicit compute_area_multiplier from the sub-tile scheduler.",
        "Measured full-value tile and softmax-weight generator PPA are used for local datapath overhead only.",
        "The dense GEMM compute array is treated as already packed into the current logic budget; extra dual-stream compute must fit that same budget to be feasible.",
        "Buffer capacity is checked against measured local SRAM bytes; an optional buffer-area proxy can be added for sensitivity but defaults to zero to avoid double-counting measured local SRAM.",
    ]
    if composed_variants:
        assumptions.append(
            "When composed dual-stream wrapper substitution is enabled, full-value and softmax measurements are treated as folded into the measured dual-stream RTL wrapper, and wrapper clock is used to scale feasible latency if it differs from source schedule clock."
        )
    if command_dispatch_control_variants:
        assumptions.append(
            "When command-dispatch control metrics are provided, the smallest measured dispatcher variant covering the schedule cluster count is added as a central logic-area and power term; its clock must meet the schedule clock for measured-control feasibility."
        )
    if not composed_variants and compute_block:
        assumptions.append(
            "When compute-block substitution is enabled, measured block area/power/clock replace the source dense compute block, but the upstream schedule latency is not recomputed; this is an area-feasibility substitution and a conservative latency view when the substituted block clock is no slower than the source clock."
        )
    elif not composed_variants:
        assumptions.append("No compute-block substitution was requested; dense compute area comes from the source schedule.")
    return {
        "version": 1,
        "model": args.model_name,
        "subtile_pipeline_json": str(args.subtile_pipeline_json),
        "source_model": source.get("model"),
        "inputs": {
            "frontier_row_limit": args.frontier_row_limit,
            "full_value_tile_metrics": str(args.full_value_tile_metrics),
            "softmax_weight_metrics": str(args.softmax_weight_metrics),
            "composed_dual_stream_metrics": (
                [str(path) for path in composed_dual_stream_metrics] if composed_dual_stream_metrics else None
            ),
            "command_dispatch_control_metrics": (
                [str(path) for path in command_dispatch_control_metrics]
                if command_dispatch_control_metrics
                else None
            ),
            "compute_block_metrics": str(args.compute_block_metrics) if args.compute_block_metrics else None,
            "compute_block_macs_per_cycle": args.compute_block_macs_per_cycle,
            "compute_arch_name": args.compute_arch_name,
            "quality_gate_json": str(args.quality_gate_json) if args.quality_gate_json else None,
            "precision_profile": args.precision_profile,
            "buffer_area_um2_per_byte": args.buffer_area_um2_per_byte,
            "recompute_area_fit_replicas": args.recompute_area_fit_replicas,
            "command_cycles_per_tile": args.command_cycles_per_tile,
            "command_cycles_per_wave": args.command_cycles_per_wave,
        },
        "quality_gate": {
            "decision": (quality_gate or {}).get("diagnosis", {}).get("decision"),
            "best_low_cost_candidate": (quality_gate or {}).get("diagnosis", {}).get("best_low_cost_candidate"),
            "best_low_cost_decision": (quality_gate or {}).get("diagnosis", {}).get("best_low_cost_decision"),
            "best_quality_candidate": (quality_gate or {}).get("diagnosis", {}).get("best_quality_candidate"),
            "best_quality_decision": (quality_gate or {}).get("diagnosis", {}).get("best_quality_decision"),
        }
        if quality_gate
        else None,
        "diagnosis": {
            "decision": decision,
            "precision_profile": args.precision_profile,
            "source_rows_used": len(source_rows),
            "physical_feasible_rows": len(feasible_rows),
            "best_requested_mode": best_requested.get("compute_mode"),
            "best_requested_latency_us": best_requested.get("latency_us"),
            "best_requested_adjusted_latency_us_if_feasible": best_requested.get("adjusted_latency_us_if_feasible"),
            "best_requested_speedup_vs_hbm_closed_source": best_requested.get("latency_speedup_vs_hbm_closed_source"),
            "best_requested_adjusted_speedup_vs_hbm_closed_source": best_requested.get("adjusted_speedup_if_feasible"),
            "best_requested_adjusted_tile_service_cycles": best_requested.get("adjusted_tile_service_cycles_if_feasible"),
            "best_requested_area_fit": best_requested.get("area_fit"),
            "best_requested_logic_slack_um2": best_requested.get("logic_area_slack_required_um2"),
            "best_requested_compute_area_over_budget_um2": best_requested.get("compute_area_over_budget_um2"),
            "best_requested_required_compute_density_gain": best_requested.get("required_compute_density_gain"),
            "best_requested_compute_substitution_enabled": best_requested.get("compute_substitution_enabled"),
            "best_requested_substituted_compute_arch": best_requested.get("substituted_compute_arch"),
            "best_requested_substituted_compute_variant_label": best_requested.get("substituted_compute_variant_label"),
            "best_requested_substituted_compute_semantic_profile": best_requested.get(
                "substituted_compute_semantic_profile"
            ),
            "best_requested_substituted_compute_variant_kind": best_requested.get(
                "substituted_compute_variant_kind"
            ),
            "best_requested_substituted_compute_area_um2": best_requested.get("substituted_compute_area_um2"),
            "best_requested_compute_clock_ok": best_requested.get("compute_clock_ok"),
            "best_requested_command_dispatch_control_variant": best_requested.get(
                "measured_command_dispatch_control_variant_name"
            ),
            "best_requested_command_dispatch_control_cluster_count": best_requested.get(
                "measured_command_dispatch_control_cluster_count"
            ),
            "best_requested_command_dispatch_control_area_um2": best_requested.get(
                "measured_command_dispatch_control_area_um2"
            ),
            "best_requested_command_dispatch_control_clock_ok": best_requested.get(
                "command_dispatch_control_clock_ok"
            ),
            "best_requested_replica_recost_enabled": best_requested.get("replica_recost_enabled"),
            "best_requested_replica_recost_area_fit_replica_count": best_requested.get(
                "replica_recost_area_fit_replica_count"
            ),
            "best_requested_replica_recost_macs_per_cycle": best_requested.get("replica_recost_macs_per_cycle"),
            "best_requested_replica_recost_latency_us": best_requested.get("replica_recost_latency_us"),
            "best_feasible_mode": best_feasible.get("compute_mode") if best_feasible else None,
            "best_feasible_latency_us": _effective_latency_us(best_feasible) if best_feasible else None,
            "best_feasible_source_latency_us": best_feasible.get("latency_us") if best_feasible else None,
            "best_area_fit_mode": best_area_fit.get("compute_mode") if best_area_fit else None,
            "best_area_fit_latency_us": _effective_latency_us(best_area_fit) if best_area_fit else None,
            "best_area_fit_source_latency_us": best_area_fit.get("latency_us") if best_area_fit else None,
            "recommended_next_step": (
                "measure a denser dual-stream fused attention datapath or reduce compute replicas before promoting dual_mac"
                if decision == "dual_stream_area_blocked"
                else "promote dual-stream schedule into a measured RTL/PPA wrapper"
            ),
        },
        "best_requested": best_requested,
        "best_feasible": best_feasible,
        "best_area_fit": best_area_fit,
        "rows": rows,
        "assumptions": assumptions,
    }


def write_markdown(path: Path, payload: JsonDict) -> None:
    diag = payload["diagnosis"]
    best = payload["best_requested"]
    lines = [
        "# Llama7B Dual-Stream Physical Feasibility",
        "",
        f"- decision: `{diag['decision']}`",
        f"- precision profile: `{diag['precision_profile']}`",
        f"- source rows used: `{diag['source_rows_used']}`",
        f"- physical feasible rows: `{diag['physical_feasible_rows']}`",
        f"- best requested mode: `{diag['best_requested_mode']}`",
        f"- best requested latency us: `{diag['best_requested_latency_us']}`",
        f"- best requested logic slack um2: `{diag['best_requested_logic_slack_um2']}`",
        f"- best requested compute area over budget um2: `{diag['best_requested_compute_area_over_budget_um2']}`",
        f"- best requested required compute density gain: `{diag['best_requested_required_compute_density_gain']}`",
        f"- best requested compute substitution: `{diag['best_requested_compute_substitution_enabled']}`",
        f"- best requested substituted compute arch: `{diag['best_requested_substituted_compute_arch']}`",
        f"- best requested substituted compute variant: `{diag['best_requested_substituted_compute_variant_label']}`",
        f"- best requested substituted compute kind: `{diag['best_requested_substituted_compute_variant_kind']}`",
        f"- best requested substituted compute semantic profile: `{diag['best_requested_substituted_compute_semantic_profile']}`",
        f"- best requested substituted compute area um2: `{diag['best_requested_substituted_compute_area_um2']}`",
        f"- best requested command dispatch control variant: `{diag['best_requested_command_dispatch_control_variant']}`",
        f"- best requested command dispatch control area um2: `{diag['best_requested_command_dispatch_control_area_um2']}`",
        f"- best requested command dispatch control clock ok: `{diag['best_requested_command_dispatch_control_clock_ok']}`",
        f"- recommended next step: `{diag['recommended_next_step']}`",
        "",
        "## Best Requested",
        "",
        "| mode | latency us | speedup | area fit | buffer fit | substituted variant | semantic profile | logic slack um2 | area over budget | "
        "density gain | required replicas | budget replicas | req buffer bytes |",
        "|---|---:|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|",
        "| {compute_mode} | {latency_us} | {latency_speedup_vs_hbm_closed_source} | {area_fit} | {buffer_fit} | "
        "{substituted_compute_variant_label} | {substituted_compute_semantic_profile} | "
        "{logic_area_slack_required_um2} | {compute_area_over_budget_um2} | "
        "{required_compute_density_gain} | {replica_count_required} | "
        "{replica_count_budgeted_at_current_compute_area} | {required_stream_buffer_bytes} |".format(**best),
        "",
        "## Rows",
        "",
        "| mode | latency us | area fit | feasible | substituted variant | semantic profile | command ctrl | logic slack um2 | local datapath/cluster | compute area required |",
        "|---|---:|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {compute_mode} | {latency_us} | {area_fit} | {physical_feasible} | "
            "{substituted_compute_variant_label} | {substituted_compute_semantic_profile} | "
            "{measured_command_dispatch_control_variant_name} | "
            "{logic_area_slack_required_um2} | {selected_local_datapath_area_um2_per_cluster} | "
            "{compute_area_required_um2} |".format(**row)
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {item}" for item in payload["assumptions"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subtile-pipeline-json", type=Path, required=True)
    parser.add_argument("--full-value-tile-metrics", type=Path, required=True)
    parser.add_argument("--softmax-weight-metrics", type=Path, required=True)
    parser.add_argument("--composed-dual-stream-metrics", type=Path, action="append")
    parser.add_argument("--command-dispatch-control-metrics", type=Path, action="append")
    parser.add_argument("--compute-block-metrics", type=Path)
    parser.add_argument("--compute-block-macs-per-cycle", type=int)
    parser.add_argument("--compute-arch-name")
    parser.add_argument("--quality-gate-json", type=Path)
    parser.add_argument("--precision-profile", default="exact_q8_kv8_v16_s24_w16")
    parser.add_argument(
        "--model-name",
        default="llm_decoder_attention_kv_dual_stream_physical_feasibility_llama7b_v1",
    )
    parser.add_argument("--frontier-row-limit", type=int, default=8)
    parser.add_argument("--buffer-area-um2-per-byte", type=float, default=0.0)
    parser.add_argument(
        "--command-cycles-per-tile",
        help=(
            "Optional comma-separated command-dispatch cycle overrides per tile. "
            "When omitted, source row command cycles are preserved."
        ),
    )
    parser.add_argument(
        "--command-cycles-per-wave",
        help=(
            "Optional comma-separated command-dispatch cycle overrides per wave. "
            "When omitted, source row command cycles are preserved."
        ),
    )
    parser.add_argument(
        "--recompute-area-fit-replicas",
        action="store_true",
        help=(
            "When measured compute substitution exceeds area budget, recost a conservative point "
            "using the budgeted replica count and measured substituted clock."
        ),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    payload = build_report(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"ok": True, "out": str(args.out), "out_md": str(args.out_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
