from __future__ import annotations

import pytest

from npu.eval.model_llama7b_phase2_exact_command_scheduler import (
    REDUCTION_ADAPTER_SLOT_COUNT,
    ROOT_CLUSTER,
    ExactPhase2CommandScheduler,
    ReadinessEvent,
    SchedulerError,
    TRANSPORT_ALIGNED,
    TRANSPORT_STATS_ONCE,
    all_readiness_events,
    derive_commands,
    expected_counts,
)


def _all_events() -> tuple[ReadinessEvent, ...]:
    return all_readiness_events(shared_release_cycle=0, reduction_release_cycle=100)


@pytest.mark.parametrize(
    ("mode", "packets", "flits"),
    [
        (TRANSPORT_ALIGNED, 9536, 76288),
        (TRANSPORT_STATS_ONCE, 8876, 70948),
    ],
)
def test_contexts_preserve_exact_transport_counts(
    mode: str, packets: int, flits: int
) -> None:
    commands = derive_commands(_all_events(), transport_mode=mode, require_complete=True)
    counts = expected_counts(mode)

    assert len(commands) == 116
    assert sum(command.kind == "shared" for command in commands) == 112
    assert sum(command.kind == "reduction_group" for command in commands) == 4
    assert sum(command.packet_count for command in commands) == packets
    assert sum(command.flit_count for command in commands) == flits
    assert counts["total_context_commands"] == 116
    assert counts["total_packet_descriptors"] == packets
    assert counts["total_flits"] == flits


def test_reduction_is_one_atomic_context_per_group() -> None:
    events = all_readiness_events(
        shared_release_cycle=0,
        reduction_release_cycle=lambda group, source: 100 + group * 20 + source,
    )
    commands = derive_commands(events, transport_mode=TRANSPORT_STATS_ONCE, require_complete=True)
    reductions = [command for command in commands if command.kind == "reduction_group"]

    assert [command.group for command in reductions] == [0, 1, 2, 3]
    assert all(command.sources == tuple(range(ROOT_CLUSTER)) for command in reductions)
    assert [command.release_cycle for command in reductions] == [114, 134, 154, 174]
    assert reductions[0].source_release_cycles == tuple(range(100, 115))
    assert all(command.packet_count == 15 * 21 for command in reductions)
    assert all(command.flit_count == 15 * 167 for command in reductions)


def test_reduction_waits_for_last_source_without_serializing_packets() -> None:
    events = tuple(
        ReadinessEvent.reduction(
            source=source,
            group=0,
            cycle=50 if source == ROOT_CLUSTER - 1 else 0,
        )
        for source in range(ROOT_CLUSTER)
    )
    scheduler = ExactPhase2CommandScheduler(events, transport_mode=TRANSPORT_STATS_ONCE)

    for _ in range(50):
        step = scheduler.step()
        assert step.valid is False
        assert step.fired is False

    first = scheduler.step()
    assert first.fired is True
    assert first.command is not None
    assert first.command.kind == "reduction_group"
    assert first.command.issue_cycle == 50
    assert scheduler.done is True


def test_storage_binding_matches_embodied_adapter_ownership() -> None:
    commands = derive_commands(_all_events(), transport_mode=TRANSPORT_STATS_ONCE)
    reductions = [command for command in commands if command.kind == "reduction_group"]
    shared = [command for command in commands if command.kind == "shared"]

    assert reductions
    assert all(command.storage_slot_count == REDUCTION_ADAPTER_SLOT_COUNT for command in reductions)
    assert all(
        command.storage_binding == "adapter_owned_dynamic_two_slot_ping_pong"
        for command in reductions
    )
    assert all(
        command.completion_binding == "shared_root_rx_descriptor_completion_releases_tx"
        for command in reductions
    )
    assert reductions[0].metadata["sources"] == list(range(ROOT_CLUSTER))
    assert reductions[0].metadata["packet_count"] == 315
    assert reductions[0].metadata["latency_evidence"] == (
        "none_without_measured_destination_ready_trace"
    )

    assert shared
    assert all(command.storage_slot_count is None for command in shared)
    assert all(command.storage_binding == "external_shared_sram_residency_completion" for command in shared)


def test_shared_context_preserves_producer_addresses_and_variable_packet_count() -> None:
    commands = derive_commands(
        [
            ReadinessEvent.shared(
                wave=0,
                cluster=3,
                cycle=7,
                source_base_addr=0x0100_3000,
                destination_base_addr=0x0200_3000,
                packet_count=3,
            )
        ]
    )

    assert len(commands) == 1
    command = commands[0]
    assert command.packet_count == 3
    assert command.flit_count == 24
    assert command.source_base_addr == 0x0100_3000
    assert command.destination_base_addr == 0x0200_3000
    assert command.metadata["source_base_addr"] == 0x0100_3000

    legacy_mapping = derive_commands(
        [{"kind": "shared", "wave": 0, "cluster": 0, "cycle": 0}]
    )[0]
    assert legacy_mapping.packet_count == 68


@pytest.mark.parametrize(
    "event",
    [
        ReadinessEvent.shared(wave=0, cluster=0, cycle=0, packet_count=0),
        ReadinessEvent.shared(
            wave=0,
            cluster=0,
            cycle=0,
            source_base_addr=0x101,
        ),
        ReadinessEvent.shared(
            wave=0,
            cluster=0,
            cycle=0,
            destination_base_addr=-256,
        ),
    ],
)
def test_shared_context_rejects_invalid_physical_metadata(event: ReadinessEvent) -> None:
    with pytest.raises(SchedulerError):
        ExactPhase2CommandScheduler([event])


def test_round_robin_context_arbitration_is_deterministic_and_fair() -> None:
    events = (
        ReadinessEvent.shared(wave=0, cluster=0, cycle=0),
        ReadinessEvent.shared(wave=0, cluster=1, cycle=0),
    )
    first = ExactPhase2CommandScheduler(events)
    second = ExactPhase2CommandScheduler(events)

    assert first.run() == second.run()
    assert [command.context_id for command in first.accepted_commands] == [
        "shared:w0:c0",
        "shared:w0:c1",
    ]


def test_missing_stream_is_not_assumed_ready() -> None:
    commands = derive_commands(
        (
            ReadinessEvent.shared(wave=0, cluster=0, cycle=20),
            ReadinessEvent.shared(wave=0, cluster=1, cycle=0),
        )
    )

    assert len(commands) == 2
    assert commands[0].context_id == "shared:w0:c1"
    assert commands[1].context_id == "shared:w0:c0"


def test_selected_context_is_stable_under_backpressure() -> None:
    scheduler = ExactPhase2CommandScheduler(
        [ReadinessEvent.shared(wave=0, cluster=0, cycle=0)]
    )
    selected = scheduler.peek()
    assert selected is not None

    stalled = scheduler.step(output_ready=False)
    assert stalled.valid is True
    assert stalled.fired is False
    assert stalled.command == selected
    assert scheduler.peek() == selected

    accepted = scheduler.step(output_ready=True)
    assert accepted.fired is True
    assert accepted.command is not None
    assert accepted.command.issue_cycle == 1


def test_duplicate_regressing_and_invalid_events_are_rejected() -> None:
    event = ReadinessEvent.shared(wave=0, cluster=0, cycle=4)
    with pytest.raises(SchedulerError, match="duplicate"):
        ExactPhase2CommandScheduler([event, event])
    with pytest.raises(SchedulerError, match="regressed"):
        ExactPhase2CommandScheduler(
            [event, ReadinessEvent.shared(wave=0, cluster=0, cycle=3)]
        )
    with pytest.raises(SchedulerError, match="invalid transport mode"):
        ExactPhase2CommandScheduler([], transport_mode="per_wave_static")


def test_partial_reduction_group_is_not_a_context() -> None:
    scheduler = ExactPhase2CommandScheduler(
        [ReadinessEvent.reduction(source=0, group=0, cycle=0)]
    )
    assert scheduler.done is True
    assert scheduler.peek() is None
    assert scheduler.complete_workload is False


def test_complete_requirement_reports_missing_readiness() -> None:
    scheduler = ExactPhase2CommandScheduler([])
    assert scheduler.done is True
    assert scheduler.complete_workload is False
    with pytest.raises(SchedulerError, match="missing readiness"):
        scheduler.require_complete_events()
