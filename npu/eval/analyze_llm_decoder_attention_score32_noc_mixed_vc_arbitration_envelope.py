#!/usr/bin/env python3
"""Sweep shared-mesh VC0/VC1 arbitration over the unknown release offset."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from npu.eval.generate_llm_decoder_attention_score32_noc_exact_router_rtl_activity import (  # noqa: E402
    ExactRouterPhase,
    build_exact_phase_models,
)
from npu.sim.perf.attention_exact_mixed_vc_router import (  # noqa: E402
    PositionedRouterPhase,
    simulate_mixed_vc_router_replay,
)

JsonDict = dict[str, Any]

SHARED_CONTEXTS = 112
SHARED_PACKETS = 7_616
SHARED_FLITS = 60_928
REDUCTION_CONTEXTS_PER_GROUP = 15
REDUCTION_PACKETS_PER_GROUP = 315
REDUCTION_FLITS_PER_GROUP = 2_505


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_hashes(repo_root: Path) -> JsonDict:
    paths = (
        Path("npu/eval/analyze_llm_decoder_attention_score32_noc_mixed_vc_arbitration_envelope.py"),
        Path("npu/eval/generate_llm_decoder_attention_score32_noc_exact_router_rtl_activity.py"),
        Path("npu/sim/perf/attention_exact_mixed_vc_router.py"),
        Path("npu/sim/perf/attention_shared_stream_context_service.py"),
        Path("npu/sim/perf/stats_once_shared_root.py"),
        Path("npu/sim/perf/noc_sram_packet_mesh.py"),
        Path("npu/sim/perf/noc_segmented_mesh.py"),
        Path("npu/sim/rtl/noc_segmented_mesh_router.sv"),
    )
    return {path.as_posix(): _sha256(repo_root / path) for path in paths}


def _service_cycles(phase: ExactRouterPhase) -> int:
    value = phase.mesh_result.cycles if phase.service_cycles is None else phase.service_cycles
    if value <= 0:
        raise ValueError(f"phase {phase.name} has a non-positive service duration")
    return int(value)


def _positioned_phases(
    shared: ExactRouterPhase,
    reductions: tuple[ExactRouterPhase, ...],
    *,
    reduction_base_cycle: int,
) -> tuple[PositionedRouterPhase, ...]:
    rows = [PositionedRouterPhase(shared, 0)]
    offset = reduction_base_cycle
    for phase in reductions:
        rows.append(PositionedRouterPhase(phase, offset))
        offset += _service_cycles(phase)
    return tuple(rows)


def _validate_exact_phase_contract(
    shared: ExactRouterPhase,
    reductions: tuple[ExactRouterPhase, ...],
) -> None:
    shared_identity = (
        shared.name,
        shared.transport_class,
        shared.context_count,
        shared.packet_count,
        shared.flit_count,
    )
    expected_shared_identity = (
        "shared_vc0_full_context_service",
        "shared_sram_context_vc0",
        SHARED_CONTEXTS,
        SHARED_PACKETS,
        SHARED_FLITS,
    )
    if shared_identity != expected_shared_identity:
        raise ValueError(
            "VC0 phase differs from the exact full-context contract: "
            f"expected={expected_shared_identity!r} observed={shared_identity!r}"
        )
    for group, phase in enumerate(reductions):
        identity = (
            phase.name,
            phase.transport_class,
            phase.context_count,
            phase.packet_count,
            phase.flit_count,
        )
        expected = (
            f"reduction_vc1_group_{group}",
            "stats_once_exact_reduction_vc1",
            REDUCTION_CONTEXTS_PER_GROUP,
            REDUCTION_PACKETS_PER_GROUP,
            REDUCTION_FLITS_PER_GROUP,
        )
        if identity != expected:
            raise ValueError(
                f"VC1 group {group} differs from the exact reduction contract: "
                f"expected={expected!r} observed={identity!r}"
            )


def analyze(
    phases: Iterable[ExactRouterPhase],
    *,
    overlap_fractions: Iterable[float],
    policies: Iterable[str],
    max_cycles: int = 250_000,
) -> JsonDict:
    phase_rows = tuple(phases)
    shared_rows = [phase for phase in phase_rows if phase.group is None]
    reductions = tuple(
        sorted(
            (phase for phase in phase_rows if phase.group is not None),
            key=lambda row: int(row.group),
        )
    )
    if len(shared_rows) != 1 or [phase.group for phase in reductions] != [0, 1, 2, 3]:
        raise ValueError("exact envelope requires one VC0 phase and VC1 groups 0,1,2,3")
    shared = shared_rows[0]
    _validate_exact_phase_contract(shared, reductions)
    fractions = tuple(float(value) for value in overlap_fractions)
    if not fractions or any(value < 0.0 or value > 1.0 for value in fractions):
        raise ValueError("overlap fractions must be a non-empty subset of [0, 1]")
    policy_rows = tuple(str(value) for value in policies)
    if not policy_rows:
        raise ValueError("at least one endpoint injection policy is required")

    shared_service = _service_cycles(shared)
    reduction_service = sum(_service_cycles(phase) for phase in reductions)
    total_flits = sum(phase.flit_count for phase in phase_rows)
    reduction_tail = max(
        _service_cycles(phase) - phase.mesh_result.cycles for phase in reductions
    )
    rows: list[JsonDict] = []
    for policy in policy_rows:
        for fraction in fractions:
            reduction_base = int(round(fraction * shared_service))
            positioned = _positioned_phases(
                shared,
                reductions,
                reduction_base_cycle=reduction_base,
            )
            replay = simulate_mixed_vc_router_replay(
                positioned,
                endpoint_injection_policy=policy,
                max_cycles=max_cycles,
            )
            rows.append(
                {
                    "case_id": f"{policy}_offset_{fraction:.2f}",
                    "endpoint_injection_policy": policy,
                    "reduction_base_fraction_of_vc0_service": fraction,
                    "reduction_base_cycle": reduction_base,
                    "phase_offsets": dict(replay.phase_offsets),
                    "router_drain_cycles": replay.mesh.cycles,
                    "transport_completion_bound_cycles": replay.mesh.cycles + reduction_tail,
                    "isolated_router_completion_cycle": replay.isolated_router_completion_cycle,
                    "router_completion_delta_cycles": replay.router_completion_delta_cycles,
                    "mesh_contention_cycles": replay.mesh_contention_cycles,
                    "router_contention_cycles_total": replay.router_contention_cycles_total,
                    "endpoint_input_stall_cycles_total": sum(
                        replay.mesh.endpoint_input_stall_cycles
                    ),
                    "max_router_input_occupancy": replay.max_router_input_occupancy,
                    "max_source_queue_occupancy": replay.max_source_queue_occupancy,
                    "max_source_vc_queue_occupancy": list(
                        replay.max_source_vc_queue_occupancy
                    ),
                    "one_register_source_capacity_sufficient": replay.one_register_source_capacity_sufficient,
                    "isolated_release_schedule_preserved": replay.isolated_release_schedule_preserved,
                    "directly_replayable_at_current_source_boundary": (
                        replay.directly_replayable_at_current_source_boundary
                    ),
                    "delivered_flits_by_phase": dict(replay.delivered_flits_by_phase),
                    "delivered_flits_by_vc": {
                        str(vc): count for vc, count in replay.delivered_flits_by_vc
                    },
                }
            )

    best_router = min(rows, key=lambda row: int(row["router_drain_cycles"]))
    directly_realizable = [
        row
        for row in rows
        if bool(row["directly_replayable_at_current_source_boundary"])
    ]
    directly_realizable_overlap = [
        row
        for row in directly_realizable
        if float(row["reduction_base_fraction_of_vc0_service"]) < 1.0
    ]
    decision = (
        "shared_mesh_has_one_register_feasible_overlap_point"
        if directly_realizable_overlap
        else "shared_mesh_overlap_requires_backpressure_coupled_endpoint_replay"
    )
    return {
        "version": 1,
        "model": "llama7b_score32_exact_mixed_vc_router_arbitration_envelope",
        "decision": decision,
        "source_contract": {
            "precision": "exact_score32_stats_once",
            "shared_contexts": 112,
            "shared_packets": 7_616,
            "shared_flits": 60_928,
            "reduction_groups": 4,
            "reduction_packets": 1_260,
            "reduction_flits": 10_020,
            "total_flits": total_flits,
            "mesh": "4x4_deterministic_xy_registered_credit_vc4_depth4",
            "shared_vc": 0,
            "reduction_vc": 1,
        },
        "isolated_phase_service": {
            "shared_service_cycles": shared_service,
            "reduction_service_cycles_total": reduction_service,
            "dual_network_parallel_completion_cycles": max(
                shared_service, reduction_service
            ),
            "single_mesh_nonoverlap_completion_cycles": shared_service
            + reduction_service,
            "reduction_replay_tail_cycles": reduction_tail,
            "phases": [
                {
                    "name": phase.name,
                    "group": phase.group,
                    "router_cycles": phase.mesh_result.cycles,
                    "service_cycles": _service_cycles(phase),
                    "flit_count": phase.flit_count,
                }
                for phase in phase_rows
            ],
        },
        "release_envelope": {
            "axis": "first_vc1_group_admission_relative_to_vc0_service_start",
            "fractions": list(fractions),
            "vc1_group_order": "sequential_adapter_lifecycle",
            "source_timing_contract": "isolated_phase_injection_cycles_continue_while_shared_mesh_queue_backpressures",
            "interpretation": "max_source_queue_occupancy_is_the_buffer_depth_required_by_each_replay_point",
            "direct_replay_gate": "per_vc_queue_depth_at_most_one_and_zero_endpoint_injection_stalls",
            "authoritative_readiness_available": False,
            "missing_readiness": [
                "shared SRAM residency cycles from the external HBM/fill producer",
                "cycle-aligned local-reducer beat-valid traces from the integrated hierarchy",
            ],
        },
        "rows": rows,
        "summary": {
            "case_count": len(rows),
            "directly_replayable_case_count": len(directly_realizable),
            "directly_replayable_overlap_case_count": len(
                directly_realizable_overlap
            ),
            "minimum_router_drain_case_id": best_router["case_id"],
            "minimum_router_drain_cycles": best_router["router_drain_cycles"],
            "minimum_router_drain_required_source_queue": best_router[
                "max_source_queue_occupancy"
            ],
            "minimum_directly_replayable_case_id": (
                min(directly_realizable, key=lambda row: int(row["router_drain_cycles"]))[
                    "case_id"
                ]
                if directly_realizable
                else None
            ),
            "promotable_overlap_case_id": (
                min(
                    directly_realizable_overlap,
                    key=lambda row: int(row["router_drain_cycles"]),
                )["case_id"]
                if directly_realizable_overlap
                else None
            ),
        },
        "remaining_abstractions": [
            "The relative VC0/VC1 producer release schedule is swept because "
            "the checked integrated artifact has no cycle-aligned readiness trace.",
            "Isolated endpoint injection traces are queued during shared-mesh "
            "backpressure; any point with an endpoint injection stall or more "
            "than one queued flit per VC needs a backpressure-coupled endpoint "
            "replay before promotion.",
            "The shared local endpoint VC arbiter is modeled cycle-accurately "
            "but is not yet embodied and equivalence-checked as RTL.",
            "HBM/DRAM control and PHY remain external by design.",
        ],
    }


def render_markdown(report: JsonDict) -> str:
    isolated = report["isolated_phase_service"]
    lines = [
        "# Exact mixed-VC router arbitration envelope",
        "",
        f"Decision: `{report['decision']}`",
        "",
        "| Case | Policy | VC1 offset | Router cycles | Completion delta | "
        "Mesh contention | Source queue | Source stalls | Direct replay |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        lines.append(
            f"| {row['case_id']} | {row['endpoint_injection_policy']} | "
            f"{row['reduction_base_cycle']} | {row['router_drain_cycles']} | "
            f"{row['router_completion_delta_cycles']} | {row['mesh_contention_cycles']} | "
            f"{row['max_source_queue_occupancy']} | "
            f"{row['endpoint_input_stall_cycles_total']} | "
            f"{str(row['directly_replayable_at_current_source_boundary']).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Baselines",
            "",
            f"- Dual-network parallel completion: `{isolated['dual_network_parallel_completion_cycles']}` cycles.",
            f"- Single-mesh non-overlap completion: `{isolated['single_mesh_nonoverlap_completion_cycles']}` cycles.",
            f"- Exact transported flits: `{report['source_contract']['total_flits']}`.",
            "",
            "## Interpretation",
            "",
            "The offset sweep is an envelope, not a measured producer schedule. "
            "A row is directly replayable only when every per-VC source queue "
            "stays at depth one or less and endpoint injection never stalls. "
            "Otherwise the fixed isolated release schedule is not preserved and "
            "a backpressure-coupled replay is required.",
            "",
            "## Remaining Abstractions",
            "",
        ]
    )
    lines.extend(f"- {value}" for value in report["remaining_abstractions"])
    lines.append("")
    return "\n".join(lines)


def _csv_floats(value: str) -> tuple[float, ...]:
    return tuple(float(part) for part in value.split(",") if part.strip())


def _csv_strings(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument(
        "--overlap-fractions",
        type=_csv_floats,
        default=_csv_floats("0,0.25,0.5,0.75,1"),
    )
    parser.add_argument(
        "--policies",
        type=_csv_strings,
        default=_csv_strings("vc_round_robin,fifo"),
    )
    parser.add_argument("--max-cycles", type=int, default=250_000)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    report = analyze(
        build_exact_phase_models(),
        overlap_fractions=args.overlap_fractions,
        policies=args.policies,
        max_cycles=args.max_cycles,
    )
    report["source_hashes"] = _source_hashes(repo_root)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
