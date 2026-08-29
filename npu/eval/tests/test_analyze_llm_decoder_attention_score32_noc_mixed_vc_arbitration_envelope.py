from __future__ import annotations

from types import SimpleNamespace

from npu.eval import (
    analyze_llm_decoder_attention_score32_noc_mixed_vc_arbitration_envelope as envelope,
)


def _phases() -> tuple[SimpleNamespace, ...]:
    shared = SimpleNamespace(
        name="shared_vc0_full_context_service",
        transport_class="shared_sram_context_vc0",
        group=None,
        mesh_result=SimpleNamespace(cycles=90),
        service_cycles=100,
        context_count=112,
        packet_count=7_616,
        flit_count=60_928,
    )
    reductions = tuple(
        SimpleNamespace(
            name=f"reduction_vc1_group_{group}",
            transport_class="stats_once_exact_reduction_vc1",
            group=group,
            mesh_result=SimpleNamespace(cycles=20),
            service_cycles=25,
            context_count=15,
            packet_count=315,
            flit_count=2_505,
        )
        for group in range(4)
    )
    return (shared, *reductions)


def test_analyzer_does_not_promote_buffer_hungry_overlap(monkeypatch) -> None:
    def fake_replay(positioned, *, endpoint_injection_policy, max_cycles):
        assert endpoint_injection_policy == "vc_round_robin"
        assert max_cycles == 1000
        base = positioned[1].offset_cycles
        feasible = base == 100
        mesh = SimpleNamespace(
            cycles=195 if feasible else 150,
            endpoint_input_stall_cycles=(0,) * 16,
        )
        drains = {
            row.phase.name: row.phase.mesh_result.cycles for row in positioned
        }
        isolated_bound = max(
            row.offset_cycles + drains[row.phase.name] for row in positioned
        )
        return SimpleNamespace(
            mesh=mesh,
            phase_offsets=tuple(
                (row.phase.name, row.offset_cycles) for row in positioned
            ),
            last_delivery_cycle_by_phase=tuple(
                (
                    row.phase.name,
                    row.offset_cycles + drains[row.phase.name] - 1,
                )
                for row in positioned
            ),
            isolated_router_drain_cycles_by_phase=tuple(drains.items()),
            isolated_router_drain_bound_cycles=isolated_bound,
            router_completion_delta_cycles=mesh.cycles - isolated_bound,
            mesh_contention_cycles=10,
            router_contention_cycles_total=20,
            max_router_input_occupancy=4,
            max_source_queue_occupancy=1 if feasible else 128,
            max_source_vc_queue_occupancy=(1, 1, 0, 0)
            if feasible
            else (128, 16, 0, 0),
            one_register_source_capacity_sufficient=feasible,
            isolated_release_schedule_preserved=feasible,
            directly_replayable_at_current_source_boundary=feasible,
            delivered_flits_by_phase=tuple(
                (row.phase.name, row.phase.flit_count) for row in positioned
            ),
            delivered_flits_by_vc=((0, 60_928), (1, 10_020)),
        )

    monkeypatch.setattr(envelope, "simulate_mixed_vc_router_replay", fake_replay)
    report = envelope.analyze(
        _phases(),
        overlap_fractions=(0.0, 1.0),
        policies=("vc_round_robin",),
        max_cycles=1000,
    )

    assert report["decision"] == (
        "shared_mesh_overlap_requires_backpressure_coupled_endpoint_replay"
    )
    assert report["summary"]["directly_replayable_case_count"] == 1
    assert report["summary"]["directly_replayable_overlap_case_count"] == 0
    assert report["summary"]["minimum_router_drain_case_id"].endswith("0.00")
    assert report["summary"]["minimum_directly_replayable_case_id"].endswith(
        "1.00"
    )
    assert report["summary"]["promotable_overlap_case_id"] is None
    assert report["source_contract"]["total_flits"] == 70_948
    nonoverlap = next(
        row
        for row in report["rows"]
        if row["reduction_base_fraction_of_vc0_service"] == 1.0
    )
    assert nonoverlap["router_completion_delta_cycles"] == 0
    assert nonoverlap["transport_completion_bound_cycles"] == 200


def test_analyzer_rejects_wrong_exact_phase_cardinality() -> None:
    phases = list(_phases())
    phases[0] = SimpleNamespace(**{**vars(phases[0]), "flit_count": 60_927})
    try:
        envelope.analyze(
            phases,
            overlap_fractions=(0.0,),
            policies=("vc_round_robin",),
        )
    except ValueError as exc:
        assert "exact full-context contract" in str(exc)
    else:
        raise AssertionError("wrong exact phase cardinality was accepted")


def test_analyzer_rejects_incomplete_exact_phase_set() -> None:
    phases = _phases()[:-1]
    try:
        envelope.analyze(
            phases,
            overlap_fractions=(0.0,),
            policies=("vc_round_robin",),
        )
    except ValueError as exc:
        assert "groups 0,1,2,3" in str(exc)
    else:
        raise AssertionError("incomplete exact phase set was accepted")
