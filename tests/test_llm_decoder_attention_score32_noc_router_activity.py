from __future__ import annotations

from npu.eval.generate_llm_decoder_attention_score32_noc_router_activity import (
    build_router_activity_manifest,
)
from npu.sim.perf.noc_segmented_mesh import (
    TrafficFlow,
    packetize_traffic_flow,
    simulate_scheduled_flits,
)


def _mesh(*, backpressure: bool = False):
    flows = (
        TrafficFlow(name="early", source=1, destination=0, payload_bytes=64, vc=0),
        TrafficFlow(
            name="late",
            source=1,
            destination=0,
            payload_bytes=32,
            vc=1,
            release_cycle=100,
        ),
    )
    scheduled = [item for flow in flows for item in packetize_traffic_flow(flow)]
    ready = None
    if backpressure:
        ready = [[True] * 16 for _ in range(120)]
        ready[4][0] = False
    return simulate_scheduled_flits(
        scheduled,
        endpoint_out_ready_schedule=ready,
        max_cycles=120,
        fast_forward_idle=True,
        capture_router_replay_nodes=(0,),
    )


def _manifest(mesh):
    return build_router_activity_manifest(
        mesh,
        node=0,
        source_schedule_path="schedule.json",
        source_schedule_sha256="a" * 64,
        source_schedule_semantic_sha256="b" * 64,
        clock_period_ns=1.0,
    )


def test_router_activity_manifest_is_deterministic_and_restores_idle_cycles() -> None:
    first = _manifest(_mesh())
    second = _manifest(_mesh())

    assert first == second
    assert first["equivalence"]["status"] == "pass"
    assert first["equivalence"]["checked_cycles"] == first["clock_cycles"]
    assert first["activity_counts"]["restored_idle_cycles"] > 0
    assert first["router_counters"]["current_input_occupancy"] == 0
    assert len(first["replay_contract"]["replay_signal_sha256"]) == 64


def test_router_activity_hash_changes_with_exact_ready_trace() -> None:
    baseline = _manifest(_mesh())
    stalled = _manifest(_mesh(backpressure=True))

    assert (
        baseline["replay_contract"]["replay_signal_sha256"]
        != stalled["replay_contract"]["replay_signal_sha256"]
    )
    assert stalled["activity_counts"]["nondefault_backpressure_cycles"] > 0
