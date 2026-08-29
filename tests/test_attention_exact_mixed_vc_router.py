from __future__ import annotations

from dataclasses import dataclass

import pytest

from npu.sim.perf.attention_exact_mixed_vc_router import (
    PositionedRouterPhase,
    simulate_mixed_vc_router_replay,
)
from npu.sim.perf.noc_segmented_mesh import (
    MeshSimulationResult,
    TrafficFlow,
    packetize_traffic_flow,
    simulate_scheduled_flits,
)


@dataclass(frozen=True)
class _Phase:
    name: str
    mesh_result: MeshSimulationResult
    flit_count: int
    service_cycles: int | None = None


def _phase(name: str, *, vc: int, source: int, destination: int, flits: int) -> _Phase:
    flow = TrafficFlow(
        name=name,
        source=source,
        destination=destination,
        payload_bytes=flits * 32,
        packet_payload_bytes=32,
        vc=vc,
    )
    mesh = simulate_scheduled_flits(packetize_traffic_flow(flow), max_cycles=128)
    return _Phase(name=name, mesh_result=mesh, flit_count=flits)


def test_mixed_router_replay_preserves_each_phase_and_vc_count() -> None:
    shared = _phase("shared", vc=0, source=0, destination=15, flits=4)
    reduction = _phase("reduction", vc=1, source=0, destination=15, flits=3)

    result = simulate_mixed_vc_router_replay(
        (
            PositionedRouterPhase(shared, 0),
            PositionedRouterPhase(reduction, 0),
        ),
        max_cycles=128,
    )

    assert dict(result.delivered_flits_by_phase) == {"shared": 4, "reduction": 3}
    assert dict(result.delivered_flits_by_vc) == {0: 4, 1: 3}
    assert result.mesh.endpoint_injected_flit_count == 7
    assert result.max_source_vc_queue_occupancy[0] >= 1
    assert result.max_source_vc_queue_occupancy[1] >= 1


def test_fifo_replay_reports_per_vc_source_occupancy() -> None:
    shared = _phase("shared", vc=0, source=0, destination=15, flits=2)
    reduction = _phase("reduction", vc=1, source=0, destination=15, flits=2)

    result = simulate_mixed_vc_router_replay(
        (
            PositionedRouterPhase(shared, 0),
            PositionedRouterPhase(reduction, 0),
        ),
        endpoint_injection_policy="fifo",
        max_cycles=128,
    )

    assert result.max_source_vc_queue_occupancy[0] >= 1
    assert result.max_source_vc_queue_occupancy[1] >= 1


def test_mixed_router_replay_applies_phase_offset() -> None:
    first = _phase("first", vc=0, source=0, destination=1, flits=1)
    second = _phase("second", vc=1, source=0, destination=1, flits=1)

    result = simulate_mixed_vc_router_replay(
        (
            PositionedRouterPhase(first, 0),
            PositionedRouterPhase(second, 20),
        ),
        max_cycles=64,
    )

    delivery_cycles = {
        delivery.flit.label.split("::", 1)[0]: delivery.cycle
        for delivery in result.mesh.deliveries
    }
    assert delivery_cycles["second"] >= 20
    assert result.phase_offsets == (("first", 0), ("second", 20))


def test_mixed_router_replay_rejects_duplicate_phase_names() -> None:
    phase = _phase("duplicate", vc=0, source=0, destination=1, flits=1)
    with pytest.raises(ValueError, match="names must be unique"):
        simulate_mixed_vc_router_replay(
            (
                PositionedRouterPhase(phase, 0),
                PositionedRouterPhase(phase, 1),
            )
        )
