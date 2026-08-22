from __future__ import annotations

import pytest

from npu.sim.perf.attention_shared_sram_gqa8_tensor_layout import (
    interleaved_bank,
    interleaved_row,
    k_beat_offset,
    shared_word_address,
)
from npu.sim.perf.attention_shared_sram_k_round_scheduler import (
    COMPUTE_CYCLES,
    GROUP_DIMENSIONS,
    ROUNDS_PER_GROUP,
    TOTAL_ROUNDS,
    TOTAL_STORAGE_BITS,
    WINDOW_WORDS,
    WORDS_PER_GROUP,
    SharedSramKRoundScheduler,
    round_valid_words,
    round_word_address,
    round_word_addresses,
)


def test_round_word_addresses_follow_block_major_stride_eight_layout() -> None:
    address0 = round_word_address(kv_head=2, group_index=3, round_index=0, round_slot=0)
    expected0 = k_beat_offset(kv_head=2, stream=0, block_slot=0, dimension=3 * GROUP_DIMENSIONS)
    assert address0.byte_offset == expected0
    assert address0.word_index == shared_word_address(expected0)
    assert address0.bank == interleaved_bank(expected0)
    assert address0.row == interleaved_row(expected0)

    address1 = round_word_address(kv_head=2, group_index=3, round_index=0, round_slot=1)
    expected1 = k_beat_offset(kv_head=2, stream=0, block_slot=1, dimension=3 * GROUP_DIMENSIONS)
    assert address1.byte_offset == expected1
    assert address1.byte_offset - address0.byte_offset == 1024
    assert address1.word_index - address0.word_index == 8

    address17 = round_word_address(kv_head=2, group_index=3, round_index=1, round_slot=0)
    expected17 = k_beat_offset(kv_head=2, stream=0, block_slot=17, dimension=3 * GROUP_DIMENSIONS)
    assert address17.byte_offset == expected17
    assert address17.word_index == shared_word_address(expected17)
    assert address17.bank == interleaved_bank(expected17)
    assert address17.row == interleaved_row(expected17)

    address127 = round_word_address(kv_head=2, group_index=7, round_index=7, round_slot=8)
    expected127 = k_beat_offset(kv_head=2, stream=1, block_slot=63, dimension=7 * GROUP_DIMENSIONS)
    assert address127.byte_offset == expected127
    assert address127.word_index == shared_word_address(expected127)
    assert address127.bank == interleaved_bank(expected127)
    assert address127.row == interleaved_row(expected127)

    assert round_valid_words(7) == 9
    assert len(round_word_addresses(kv_head=0, group_index=0, round_index=7)) == 9


def test_scheduler_ideal_counts_match_full_eight_group_schedule() -> None:
    result = SharedSramKRoundScheduler(response_latency=1).run()
    assert len(result.round_traces) == TOTAL_ROUNDS == 64
    assert result.counters["rounds_ready"] == TOTAL_ROUNDS
    assert result.counters["rounds_completed"] == TOTAL_ROUNDS
    assert result.counters["request_count"] == WORDS_PER_GROUP * 8 == 1024
    assert result.counters["response_count"] == WORDS_PER_GROUP * 8 == 1024
    assert result.counters["compute_cycles"] == COMPUTE_CYCLES * TOTAL_ROUNDS == 1024


def test_latency_sixteen_has_no_steady_state_compute_stalls() -> None:
    result = SharedSramKRoundScheduler(response_latency=16).run()
    assert result.counters["steady_state_compute_stall_cycles"] == 0
    for previous, current in zip(result.round_traces, result.round_traces[1:]):
        assert current.compute_start_cycle == previous.compute_end_cycle + 1


def test_bank_backpressure_stretches_round_issue_and_records_wait_cycles() -> None:
    def bank_ready(cycle: int, bank: int, group_index: int, round_index: int, round_slot: int, row: int) -> bool:
        del group_index, round_index, round_slot, row
        return not (bank == 0 and cycle < 2)

    result = SharedSramKRoundScheduler(response_latency=1, group_count=1, bank_ready_fn=bank_ready).run()
    trace0 = result.round_traces[0]
    assert trace0.issue_cycles == (0, 2)
    assert result.counters["bank_wait_cycles"] >= 2


def test_latency_above_compute_budget_introduces_steady_state_stalls() -> None:
    result = SharedSramKRoundScheduler(response_latency=17, group_count=2).run()
    assert result.counters["steady_state_compute_stall_cycles"] > 0
    assert any(
        current.compute_start_cycle > previous.compute_end_cycle + 1
        for previous, current in zip(result.round_traces, result.round_traces[1:])
    )


def test_storage_budget_and_no_overwrite_hold_under_long_latency() -> None:
    assert WINDOW_WORDS == 17
    assert TOTAL_STORAGE_BITS == 2 * 17 * 1024

    result = SharedSramKRoundScheduler(response_latency=17, group_count=1).run()
    fill_start = {
        (event.linear_round, event.buffer_id): event.cycle
        for event in result.events_of("fill_start")
    }
    release = {
        (event.linear_round, event.buffer_id): event.cycle
        for event in result.events_of("buffer_release")
    }

    assert fill_start[(2, 0)] > release[(0, 0)]
    assert fill_start[(3, 1)] > release[(1, 1)]


def test_rejects_invalid_round_buffer_configuration() -> None:
    with pytest.raises(ValueError, match="must not exceed banks"):
        SharedSramKRoundScheduler(window_words=18)

    with pytest.raises(ValueError, match="at least one cycle"):
        SharedSramKRoundScheduler(response_latency=0)


def test_round_counts_match_default_geometry() -> None:
    assert WINDOW_WORDS == 17
    assert WORDS_PER_GROUP == 128
    assert ROUNDS_PER_GROUP == 8
