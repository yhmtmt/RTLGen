#!/usr/bin/env python3
"""Audit area ownership before recosting score32 with the exact shared mesh."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

JsonDict = dict[str, Any]

_MODEL = "llm_decoder_attention_score32_exact_shared_mesh_replacement_contract_v1"
_EXACT_REDUCTION_MODEL = "llm_decoder_attention_score32_exact_reduction_recost_v1"
_FRONTIER_MODEL = "llm_decoder_attention_score32_exact_reduction_gqa8_full_equivalence_rerank_v1"
_CANDIDATE_ID = "score32_exp_lut_schedule_wrapper_hbm_controller_replay_best"
_REPLACED_COMPONENTS = ("noc_router", "noc_fifo", "onchip_endpoint")
_HIERARCHY_PREFIXES = (
    "composition/vc0_activity/service/",
    "composition/vc1_activity/exact_transport_wrapper/",
    "composition/shared_transport/",
)


def _load_json(path: Path) -> JsonDict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _finite(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _positive(value: Any, label: str) -> float:
    result = _finite(value, label)
    if result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _positive_int(value: Any, label: str) -> int:
    result = _positive(value, label)
    integer = int(result)
    if float(integer) != result:
        raise ValueError(f"{label} must be an integer")
    return integer


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _close(actual: float, expected: float, label: str, tolerance: float = 1.0e-6) -> None:
    if abs(actual - expected) > tolerance:
        raise ValueError(f"{label} mismatch: expected {expected}, got {actual}")


def _source_ref(path: Path) -> JsonDict:
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _frontier_score32_row(frontier: JsonDict) -> JsonDict:
    _require(frontier.get("model") == _FRONTIER_MODEL, "unexpected frontier model")
    rows = frontier.get("promotable_latency_rank")
    _require(isinstance(rows, list), "frontier is missing promotable_latency_rank")
    for row in rows:
        if isinstance(row, dict) and row.get("candidate_id") == _CANDIDATE_ID:
            _require(row.get("promotable") is True, "score32 frontier row must be promotable")
            _require(row.get("quality_backed") is True, "score32 frontier row must be quality backed")
            return dict(row)
    raise ValueError("frontier is missing the score32 candidate")


def build_contract(
    *,
    exact_reduction: JsonDict,
    frontier: JsonDict,
    exact_reduction_path: Path | None = None,
    frontier_path: Path | None = None,
) -> JsonDict:
    _require(exact_reduction.get("model") == _EXACT_REDUCTION_MODEL, "unexpected exact-reduction model")
    best = exact_reduction.get("best_requested")
    _require(isinstance(best, dict), "exact-reduction artifact is missing best_requested")
    row = _frontier_score32_row(frontier)

    cluster_count = _positive_int(best.get("cluster_count"), "cluster_count")
    primitive_rows: list[JsonDict] = []
    primitive_area_um2 = 0.0
    primitive_power_mw = 0.0
    for component in _REPLACED_COMPONENTS:
        count = cluster_count * _positive_int(
            best.get(f"{component}_per_cluster"), f"{component}_per_cluster"
        )
        area_each = _positive(best.get(f"{component}_area_um2"), f"{component}_area_um2")
        power_each = _positive(best.get(f"{component}_power_mw"), f"{component}_power_mw")
        primitive_area_um2 += count * area_each
        primitive_power_mw += count * power_each
        primitive_rows.append(
            {
                "component": component,
                "count": count,
                "area_um2_each": area_each,
                "area_um2_total": count * area_each,
                "vectorless_power_mw_each": power_each,
                "vectorless_power_mw_total": count * power_each,
            }
        )

    selected_l1_area_um2 = _positive(best.get("selected_l1_overhead_area_um2"), "selected_l1_overhead_area_um2")
    _close(primitive_area_um2, selected_l1_area_um2, "primitive area ownership")

    compute_area_um2 = _positive(best.get("substituted_compute_area_um2"), "substituted_compute_area_um2")
    controller = row.get("score32_hbm_controller_replay_ppa")
    _require(isinstance(controller, dict), "score32 row is missing controller PPA")
    controller_area_um2 = _positive(controller.get("controller_area_mm2"), "controller_area_mm2") * 1.0e6
    ranked_area_um2 = _positive(row.get("compute_area_mm2"), "frontier compute_area_mm2") * 1.0e6
    _close(ranked_area_um2, compute_area_um2 + controller_area_um2, "ranked score32 area ownership")

    die_area_um2 = _positive(best.get("die_area_mm2"), "die_area_mm2") * 1.0e6
    shared_sram_area_um2 = _positive(best.get("measured_shared_sram_used_area_um2"), "shared SRAM area")
    tile_local_sram_area_um2 = _positive(best.get("measured_tile_local_sram_area_um2"), "tile-local SRAM area")
    reserve_area_um2 = _positive(best.get("reserved_area_fraction"), "reserved_area_fraction") * die_area_um2
    retained_area_um2 = (
        compute_area_um2
        + controller_area_um2
        + shared_sram_area_um2
        + tile_local_sram_area_um2
        + reserve_area_um2
    )
    maximum_composed_area_um2 = die_area_um2 - retained_area_um2
    _require(maximum_composed_area_um2 > 0.0, "no die area remains for the composed hierarchy")

    source_full_embodied_area_um2 = retained_area_um2 + primitive_area_um2
    source_latency_us = _positive(row.get("latency_us"), "score32 latency")
    source_throughput = _positive(row.get("token_throughput_per_s"), "score32 throughput")
    _close(source_throughput, 1.0e6 / source_latency_us, "score32 throughput")
    source_clock_ns = _positive(best.get("replica_recost_clock_ns"), "score32 compute clock")

    inputs: JsonDict = {
        "exact_reduction_model": _EXACT_REDUCTION_MODEL,
        "frontier_model": _FRONTIER_MODEL,
        "candidate_id": _CANDIDATE_ID,
    }
    if exact_reduction_path is not None:
        inputs["exact_reduction"] = _source_ref(exact_reduction_path)
    if frontier_path is not None:
        inputs["frontier"] = _source_ref(frontier_path)

    return {
        "version": 1,
        "model": _MODEL,
        "decision": "exact_shared_mesh_replacement_boundary_recorded",
        "inputs": inputs,
        "source_frontier": {
            "latency_us": source_latency_us,
            "token_throughput_per_s": source_throughput,
            "compute_clock_ns": source_clock_ns,
            "energy_mj_per_token_lower_bound": _positive(
                row.get("energy_mj_per_token_lower_bound"), "score32 lower-bound energy"
            ),
            "energy_mj_per_token_conservative_upper_bound": _positive(
                row.get("energy_mj_per_token_conservative_upper_bound"), "score32 upper-bound energy"
            ),
            "precision_status": str(row.get("precision_status") or ""),
            "quality_backed": True,
        },
        "area_ownership": {
            "die_area_um2": die_area_um2,
            "retained_components": [
                {"component": "dual_stream_compute_replicas", "area_um2": compute_area_um2},
                {"component": "hbm_replay_controller", "area_um2": controller_area_um2},
                {"component": "shared_kv_sram", "area_um2": shared_sram_area_um2},
                {"component": "tile_local_sram", "area_um2": tile_local_sram_area_um2},
                {"component": "reserved_die_area", "area_um2": reserve_area_um2},
            ],
            "retained_area_um2": retained_area_um2,
            "source_replaced_primitive_overhead": {
                "components": primitive_rows,
                "area_um2": primitive_area_um2,
                "vectorless_power_mw": primitive_power_mw,
            },
            "source_full_embodied_area_um2": source_full_embodied_area_um2,
            "source_ranked_compute_area_um2": ranked_area_um2,
            "source_ranked_area_omits_primitive_overhead": True,
            "maximum_composed_hierarchy_area_um2": maximum_composed_area_um2,
            "recost_formula": "retained_area_um2 + measured_composed_hierarchy_area_um2",
            "replacement_delta_formula": (
                "measured_composed_hierarchy_area_um2 - source_replaced_primitive_overhead.area_um2"
            ),
        },
        "measured_replacement_contract": {
            "required_hierarchy_prefixes": list(_HIERARCHY_PREFIXES),
            "required_hierarchy_area_method": "openroad_final_odb_leaf_master_area_v1",
            "required_metric_summary_fields": [
                "critical_path_ns",
                "instance_area_um2",
                "hierarchical_instance_area_um2",
                "hierarchical_instance_count",
                "total_power_mw",
            ],
            "area_use": "hierarchical_instance_area_um2",
            "whole_harness_instance_area_use": "diagnostic_only",
            "root_stats_storage_ownership": (
                "dedicated exact-reducer state; additive to retained shared KV SRAM capacity"
            ),
            "activity_stimulus_area": "excluded_by_hierarchy_prefix",
        },
        "post_measurement_gates": {
            "area": "measured composed hierarchy area must be finite, positive, and no greater than maximum_composed_hierarchy_area_um2",
            "throughput": (
                "retain source throughput only if composed critical_path_ns does not exceed compute_clock_ns and "
                "the standalone service envelope fits the compute window and a producer-release-coupled replay "
                "proves no longer critical layer schedule"
            ),
            "energy": (
                "do not convert vectorless whole-harness power to token energy; require workload-annotated hierarchy power"
            ),
            "precision": (
                "inherit score32 quality only while full four-group exact RTL equivalence and zero protocol errors remain true"
            ),
        },
        "remaining_abstractions": [
            "composed synthesis decomposition and postroute hierarchy metrics are pending",
            "standalone service capacity is measured, but producer-release-coupled completion timing is pending",
            "workload-annotated hierarchy power is pending",
            "vendor HBM current and off-chip energy remain external",
        ],
    }


def render_markdown(report: JsonDict) -> str:
    area = report["area_ownership"]
    source = report["source_frontier"]
    lines = [
        "# Exact Shared-Mesh Replacement Contract",
        "",
        f"- source score32 throughput: `{source['token_throughput_per_s']:.12f}` token/s",
        f"- source score32 latency: `{source['latency_us']:.6f}` us/token",
        f"- source compute clock: `{source['compute_clock_ns']:.6f}` ns",
        f"- retained embodied area: `{area['retained_area_um2'] / 1.0e6:.9f}` mm2",
        f"- replaced primitive area: `{area['source_replaced_primitive_overhead']['area_um2'] / 1.0e6:.9f}` mm2",
        f"- maximum composed hierarchy area: `{area['maximum_composed_hierarchy_area_um2'] / 1.0e6:.9f}` mm2",
        "",
        "## Ownership",
        "",
    ]
    for component in area["retained_components"]:
        lines.append(f"- {component['component']}: `{component['area_um2'] / 1.0e6:.9f}` mm2")
    lines.extend(
        [
            "",
            "The current ranked compute area omits the primitive NoC/endpoint overhead. The measured composed hierarchy is therefore added directly to ranked compute area, while full embodied accounting replaces the old primitive overhead exactly once.",
            "",
            "## Gates",
            "",
        ]
    )
    for dimension, gate in report["post_measurement_gates"].items():
        lines.append(f"- {dimension}: {gate}")
    lines.extend(["", "## Remaining Abstractions", ""])
    for item in report["remaining_abstractions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exact-reduction-json", type=Path, required=True)
    parser.add_argument("--frontier-json", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args(argv)
    exact_path = args.exact_reduction_json.resolve()
    frontier_path = args.frontier_json.resolve()
    report = build_contract(
        exact_reduction=_load_json(exact_path),
        frontier=_load_json(frontier_path),
        exact_reduction_path=args.exact_reduction_json,
        frontier_path=args.frontier_json,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
