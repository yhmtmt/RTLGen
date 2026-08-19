from __future__ import annotations

import pytest

from npu.sim.perf.stats_once_banked_root import (
    packet_sram_macro_count,
    simulate_banked_stats_once_shared_root,
)


@pytest.mark.parametrize(
    ("banks", "macros"),
    [(1, 32), (2, 32), (3, 48), (4, 32), (5, 40), (8, 64), (15, 120)],
)
def test_available_macro_granularity_cost(banks: int, macros: int) -> None:
    assert packet_sram_macro_count(banks) == macros


@pytest.mark.parametrize("banks", [0, 16])
def test_macro_count_rejects_invalid_bank_count(banks: int) -> None:
    with pytest.raises(ValueError, match="physical_banks"):
        packet_sram_macro_count(banks)


def test_one_bank_is_rejected_as_macro_dominated() -> None:
    with pytest.raises(ValueError, match="dominated by four banks"):
        simulate_banked_stats_once_shared_root(physical_banks=1)


@pytest.mark.parametrize("banks", [2, 4, 8, 15])
def test_banked_replay_conserves_traffic_and_slots(banks: int) -> None:
    result = simulate_banked_stats_once_shared_root(physical_banks=banks)

    assert len(result.mesh.deliveries) == 2505
    assert len(result.replays) == 315
    assert result.max_slots_per_source <= 2
    assert result.root_delivery_span_cycles >= 2505
    assert result.final_replay_cycle >= max(row.cycle for row in result.mesh.deliveries)
    assert result.iteration_count <= 32


def test_four_banks_retain_transport_floor_at_minimum_macro_count() -> None:
    two = simulate_banked_stats_once_shared_root(physical_banks=2)
    four = simulate_banked_stats_once_shared_root(physical_banks=4)
    eight = simulate_banked_stats_once_shared_root(physical_banks=8)
    fifteen = simulate_banked_stats_once_shared_root(physical_banks=15)

    assert (two.macro_count, two.root_delivery_span_cycles, two.replay_drain_cycles) == (
        32,
        2628,
        64,
    )
    assert (four.macro_count, four.root_delivery_span_cycles, four.replay_drain_cycles) == (
        32,
        2505,
        13,
    )
    assert (eight.macro_count, eight.root_delivery_span_cycles, eight.replay_drain_cycles) == (
        64,
        2505,
        8,
    )
    assert (
        fifteen.macro_count,
        fifteen.root_delivery_span_cycles,
        fifteen.replay_drain_cycles,
    ) == (120, 2505, 8)
