from __future__ import annotations

from collections import Counter

import pytest

from npu.sim.perf.stats_once_shared_root import (
    GROUP_FLITS,
    PACKET_ROUND_RELEASE_INTERVAL_CYCLES,
    PACKETS_PER_GROUP,
    REMOTE_SOURCES,
    ROOT_ENDPOINT,
    build_shared_root_descriptors,
    packet_flit_count,
    simulate_exact_stats_once_shared_root,
)


def test_shared_root_descriptor_contract_is_exact_and_packet_major() -> None:
    descriptors = build_shared_root_descriptors(epoch=5, vc=2)

    assert len(descriptors) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert [descriptor.source for descriptor in descriptors[:REMOTE_SOURCES]] == list(
        range(REMOTE_SOURCES)
    )
    assert all(descriptor.destination == ROOT_ENDPOINT for descriptor in descriptors)
    assert all(descriptor.vc == 2 for descriptor in descriptors)
    assert descriptors[0].tag == 0xA0
    assert descriptors[-1].tag == 0xB4
    assert Counter(descriptor.flit_count for descriptor in descriptors) == {
        8: REMOTE_SOURCES * 20,
        7: REMOTE_SOURCES,
    }
    for packet in range(PACKETS_PER_GROUP):
        for source in range(REMOTE_SOURCES):
            descriptor = descriptors[packet * REMOTE_SOURCES + source]
            assert descriptor.rx_base_addr == source * 512 + (packet % 2) * 256
            assert descriptor.tx_base_addr == (packet % 2) * 256


def test_shared_root_mesh_conserves_all_exact_group_traffic() -> None:
    result = simulate_exact_stats_once_shared_root(epoch=3, vc=1)

    assert len(result.mesh.descriptors) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert len(result.mesh.rx_descriptor_handshakes) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert len(result.mesh.tx_descriptor_handshakes) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert len(result.mesh.completions) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert len(result.mesh.deliveries) == REMOTE_SOURCES * GROUP_FLITS
    assert result.mesh.max_rx_context_occupancy == REMOTE_SOURCES
    assert result.root_delivery_span_cycles >= result.serialization_lower_bound_cycles
    assert result.root_delivery_span_cycles == result.serialization_lower_bound_cycles
    assert result.serialization_lower_bound_cycles == 2505
    assert not result.mesh.protocol_errors
    assert Counter(delivery.flit.source for delivery in result.mesh.deliveries) == {
        source: GROUP_FLITS for source in range(REMOTE_SOURCES)
    }


def test_shared_root_two_slot_replay_schedule_is_feasible() -> None:
    result = simulate_exact_stats_once_shared_root()

    assert len(result.replays) == REMOTE_SOURCES * PACKETS_PER_GROUP
    assert result.max_slots_per_source <= 2
    assert result.slot_reuse_violations == ()
    assert result.packet_round_release_interval_cycles == 120
    assert result.packet_round_release_interval_cycles == (
        REMOTE_SOURCES * packet_flit_count(0)
    )
    assert PACKET_ROUND_RELEASE_INTERVAL_CYCLES == 120
    for source in range(REMOTE_SOURCES):
        source_replays = [replay for replay in result.replays if replay.source == source]
        assert [replay.packet for replay in source_replays] == list(
            range(PACKETS_PER_GROUP)
        )
        assert all(
            current.first_output_cycle > previous.final_output_cycle
            for previous, current in zip(source_replays, source_replays[1:])
        )


@pytest.mark.parametrize("packet", [-1, 21])
def test_packet_flit_count_rejects_out_of_range_packet(packet: int) -> None:
    with pytest.raises(ValueError, match="packet"):
        packet_flit_count(packet)


def test_shared_root_descriptor_builder_rejects_bad_context() -> None:
    with pytest.raises(ValueError, match="epoch"):
        build_shared_root_descriptors(epoch=8)
    with pytest.raises(ValueError, match="vc"):
        build_shared_root_descriptors(vc=4)
    with pytest.raises(ValueError, match="release"):
        build_shared_root_descriptors(release_cycles={(0, 2): -1})
