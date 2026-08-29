"""Shared-router arbitration replay for exact Phase-2 VC0/VC1 traffic.

The replay starts from the cycle-exact flits injected by independently
validated endpoint phase models.  It places those flits on one 4x4 mesh and
arbitrates endpoint injection round-robin by VC.  This closes router and local
VC arbitration for a supplied relative phase schedule, while deliberately
leaving producer release timing as a swept envelope.

An isolated producer trace continues to release flits while its shared-mesh
queue is blocked.  Queue occupancy is therefore reported as a required source
buffer bound; a point with occupancy above one is not a proof that the current
one-register ready/valid source can sustain that schedule without timing
feedback.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Iterable, Protocol

from npu.sim.perf.noc_segmented_mesh import (
    MeshSimulationResult,
    ModelFlit,
    ScheduledFlit,
    simulate_scheduled_flits,
)


class RouterPhase(Protocol):
    name: str
    mesh_result: MeshSimulationResult
    flit_count: int
    service_cycles: int | None


@dataclass(frozen=True)
class PositionedRouterPhase:
    phase: RouterPhase
    offset_cycles: int

    def __post_init__(self) -> None:
        if self.offset_cycles < 0:
            raise ValueError("phase offset must be non-negative")


@dataclass(frozen=True)
class MixedVcRouterReplay:
    mesh: MeshSimulationResult
    endpoint_injection_policy: str
    phase_offsets: tuple[tuple[str, int], ...]
    phase_flit_counts: tuple[tuple[str, int], ...]
    delivered_flits_by_phase: tuple[tuple[str, int], ...]
    delivered_flits_by_vc: tuple[tuple[int, int], ...]
    last_delivery_cycle_by_phase: tuple[tuple[str, int], ...]
    isolated_router_drain_cycles_by_phase: tuple[tuple[str, int], ...]
    isolated_router_drain_bound_cycles: int
    router_completion_delta_cycles: int
    mesh_contention_cycles: int
    router_contention_cycles_total: int
    max_router_input_occupancy: int
    max_source_queue_occupancy: int
    max_source_vc_queue_occupancy: tuple[int, ...]

    @property
    def one_register_source_capacity_sufficient(self) -> bool:
        return bool(self.max_source_vc_queue_occupancy) and all(
            value <= 1 for value in self.max_source_vc_queue_occupancy
        )

    @property
    def isolated_release_schedule_preserved(self) -> bool:
        return not any(self.mesh.endpoint_input_stall_cycles)

    @property
    def directly_replayable_at_current_source_boundary(self) -> bool:
        return (
            self.one_register_source_capacity_sufficient
            and self.isolated_release_schedule_preserved
        )


def _phase_scheduled_flits(
    positioned: PositionedRouterPhase,
    *,
    phase_order: int,
) -> tuple[ScheduledFlit, ...]:
    phase = positioned.phase
    source_ordinals = [0] * 16
    scheduled: list[ScheduledFlit] = []
    for trace in phase.mesh_result.traces:
        for source, flit in trace.injected:
            if source != flit.source:
                raise ValueError(
                    f"phase {phase.name} injection source differs from flit source"
                )
            label = f"{phase.name}::{flit.label or 'flit'}"
            scheduled.append(
                ScheduledFlit(
                    release_cycle=positioned.offset_cycles + trace.cycle,
                    schedule_order=phase_order,
                    packet_order=source_ordinals[source],
                    flit=replace(flit, label=label),
                )
            )
            source_ordinals[source] += 1
    if len(scheduled) != phase.flit_count:
        raise ValueError(
            f"phase {phase.name} injected {len(scheduled)} flits; "
            f"expected exact phase count {phase.flit_count}"
        )
    return tuple(scheduled)


def _endpoint_ready(_cycle: int, endpoint: int, flit: ModelFlit | None) -> bool:
    if flit is None or flit.vc != 0:
        return True
    # Exact VC0 destination-SRAM activity rule used by the validated complete
    # context-service phase. VC1 has a dedicated always-ready root adapter.
    return ((_cycle + endpoint) & 0xF) != 0


def _isolated_router_drain_cycles(phase: RouterPhase) -> int:
    deliveries = [
        delivery
        for trace in phase.mesh_result.traces
        for delivery in trace.deliveries
    ]
    if len(deliveries) != phase.flit_count:
        raise ValueError(
            f"phase {phase.name} recorded {len(deliveries)} isolated deliveries; "
            f"expected {phase.flit_count}"
        )
    if not deliveries:
        raise ValueError(f"phase {phase.name} has no isolated router deliveries")
    return max(delivery.cycle for delivery in deliveries) + 1


def simulate_mixed_vc_router_replay(
    phases: Iterable[PositionedRouterPhase],
    *,
    endpoint_injection_policy: str = "vc_round_robin",
    max_cycles: int = 250_000,
) -> MixedVcRouterReplay:
    positioned = tuple(phases)
    if not positioned:
        raise ValueError("at least one positioned router phase is required")
    names = [row.phase.name for row in positioned]
    if len(set(names)) != len(names):
        raise ValueError("positioned router phase names must be unique")

    scheduled = tuple(
        flit
        for phase_order, row in enumerate(positioned)
        for flit in _phase_scheduled_flits(row, phase_order=phase_order)
    )
    mesh = simulate_scheduled_flits(
        scheduled,
        endpoint_out_ready=_endpoint_ready,
        endpoint_injection_policy=endpoint_injection_policy,
        max_cycles=max_cycles,
        fast_forward_idle=True,
        record_mesh_trace=False,
        record_link_transfers=False,
    )

    delivered_by_phase: Counter[str] = Counter()
    delivered_by_vc: Counter[int] = Counter()
    last_delivery_by_phase: dict[str, int] = {}
    for delivery in mesh.deliveries:
        phase_name = delivery.flit.label.split("::", 1)[0]
        delivered_by_phase[phase_name] += 1
        delivered_by_vc[delivery.flit.vc] += 1
        last_delivery_by_phase[phase_name] = max(
            last_delivery_by_phase.get(phase_name, -1), delivery.cycle
        )

    expected_by_phase = {row.phase.name: row.phase.flit_count for row in positioned}
    if dict(delivered_by_phase) != expected_by_phase:
        raise ValueError(
            "shared-router replay did not preserve exact per-phase flit counts: "
            f"expected={expected_by_phase!r} observed={dict(delivered_by_phase)!r}"
        )
    if mesh.endpoint_injected_flit_count != len(scheduled):
        raise ValueError("shared-router replay did not inject every exact phase flit")

    isolated_drains = {
        row.phase.name: _isolated_router_drain_cycles(row.phase)
        for row in positioned
    }
    isolated_drain_bound = max(
        row.offset_cycles + isolated_drains[row.phase.name] for row in positioned
    )
    return MixedVcRouterReplay(
        mesh=mesh,
        endpoint_injection_policy=endpoint_injection_policy,
        phase_offsets=tuple((row.phase.name, row.offset_cycles) for row in positioned),
        phase_flit_counts=tuple((row.phase.name, row.phase.flit_count) for row in positioned),
        delivered_flits_by_phase=tuple(sorted(delivered_by_phase.items())),
        delivered_flits_by_vc=tuple(sorted(delivered_by_vc.items())),
        last_delivery_cycle_by_phase=tuple(sorted(last_delivery_by_phase.items())),
        isolated_router_drain_cycles_by_phase=tuple(sorted(isolated_drains.items())),
        isolated_router_drain_bound_cycles=isolated_drain_bound,
        router_completion_delta_cycles=mesh.cycles - isolated_drain_bound,
        mesh_contention_cycles=mesh.mesh_contention_cycles,
        router_contention_cycles_total=sum(
            row.arbitration_contention_cycles for row in mesh.router_summaries
        ),
        max_router_input_occupancy=max(
            row.max_input_occupancy for row in mesh.router_summaries
        ),
        max_source_queue_occupancy=mesh.max_endpoint_input_occupancy,
        max_source_vc_queue_occupancy=mesh.max_endpoint_vc_occupancy,
    )


__all__ = [
    "MixedVcRouterReplay",
    "PositionedRouterPhase",
    "simulate_mixed_vc_router_replay",
]
