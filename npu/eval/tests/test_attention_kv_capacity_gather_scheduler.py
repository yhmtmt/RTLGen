from __future__ import annotations

from collections import defaultdict

from npu.sim.perf.attention_kv_capacity_gather_scheduler import (
    ALL_PLANES,
    CONSUME,
    HBM,
    HBM_CORNER_ENDPOINTS,
    LAYERS,
    REFILL,
    RESIDENT,
    RESIDENT_BYTES_PER_LAYER,
    layer_descriptors,
    llama7b_descriptors,
)
from npu.sim.perf.attention_kv_tile_layout import BYTES_PER_KV_TILE


def test_layer_schedule_conserves_hbm_and_canonical_bytes() -> None:
    rows = layer_descriptors(0)
    assert len(rows) == 1042
    assert sum(row.operation == REFILL for row in rows) == 10
    assert sum(row.operation == CONSUME for row in rows) == 1032
    assert sum(row.payload_bytes for row in rows if row.operation == REFILL) == (
        RESIDENT_BYTES_PER_LAYER
    )
    assert sum(
        row.payload_bytes
        for row in rows
        if row.operation == CONSUME and row.source == RESIDENT
    ) == RESIDENT_BYTES_PER_LAYER
    assert sum(
        row.payload_bytes
        for row in rows
        if row.operation == CONSUME and row.source == HBM
    ) == BYTES_PER_KV_TILE * 128 - RESIDENT_BYTES_PER_LAYER
    assert sum(row.payload_bytes for row in rows if row.source == HBM) == (
        BYTES_PER_KV_TILE * 128
    )
    assert sum(row.payload_bytes for row in rows if row.operation == CONSUME) == (
        BYTES_PER_KV_TILE * 128
    )


def test_partial_tile_is_exact_monotonic_planar_split() -> None:
    rows = [
        row
        for row in layer_descriptors(0)
        if row.operation == CONSUME and row.tile == 2
    ]
    assert len(rows) == 16
    for pair_index, plane in enumerate((0, 4, 1, 5, 2, 6, 3, 7)):
        resident, hbm = rows[pair_index * 2 : pair_index * 2 + 2]
        assert resident.plane == hbm.plane == plane
        assert resident.source == RESIDENT
        assert hbm.source == HBM
        assert resident.canonical_base_address == plane * 128 * 1024
        assert resident.payload_bytes == 16 * 1024
        assert hbm.canonical_base_address == resident.canonical_base_address + 16 * 1024
        assert hbm.payload_bytes == 112 * 1024
        assert (
            resident.canonical_base_address
            + resident.payload_bytes
            == hbm.canonical_base_address
        )


def test_locality_and_hbm_corner_mapping_are_explicit() -> None:
    consume_bytes_by_cluster: dict[int, int] = defaultdict(int)
    for row in layer_descriptors(7):
        if row.operation == CONSUME:
            consume_bytes_by_cluster[row.destination_cluster] += row.payload_bytes
        if row.source == RESIDENT:
            assert row.source_endpoint == row.destination_cluster
        else:
            assert row.source_endpoint in HBM_CORNER_ENDPOINTS
    assert set(consume_bytes_by_cluster) == set(range(16))
    assert set(consume_bytes_by_cluster.values()) == {8 * BYTES_PER_KV_TILE}


def test_consume_order_matches_group_major_wave_cadence() -> None:
    rows = [row for row in layer_descriptors(0) if row.operation == CONSUME]
    cursor = 0
    for group in range(4):
        for wave in range(8):
            for plane in (group, 4 + group):
                wave_destinations: set[int] = set()
                for tile in range(wave * 16, wave * 16 + 16):
                    expected_sources = 2 if tile == 2 else 1
                    emitted = rows[cursor : cursor + expected_sources]
                    assert {row.tile for row in emitted} == {tile}
                    assert {row.plane for row in emitted} == {plane}
                    assert [row.segment for row in emitted] == (
                        [plane * 2, plane * 2 + 1]
                        if tile == 2
                        else [plane * 2]
                    )
                    wave_destinations.update(row.destination_cluster for row in emitted)
                    cursor += expected_sources
                assert wave_destinations == set(range(16))
    assert cursor == len(rows)


def test_full_schedule_boundaries_and_addresses() -> None:
    rows = llama7b_descriptors()
    assert len(rows) == LAYERS * 1042 == 33344
    assert sum(row.last for row in rows) == 1
    assert rows[-1].last
    assert rows[0].operation == REFILL
    assert rows[0].plane == ALL_PLANES
    assert rows[0].source_byte_address == 0
    assert rows[0].destination_byte_address == 0
    layer31 = layer_descriptors(31)
    assert layer31[0].source_byte_address == 31 * 128 * BYTES_PER_KV_TILE
    assert layer31[0].destination_byte_address == 31 * RESIDENT_BYTES_PER_LAYER
