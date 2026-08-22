from __future__ import annotations

import pytest

from npu.sim.perf.attention_shared_sram_gqa8_tensor_layout import (
    BLOCKS_PER_STREAM,
    interleaved_bank,
    interleaved_row,
    k_beat_offset,
    shared_word_address,
)
from npu.sim.perf.attention_shared_sram_k_window_scheduler import (
    COMPUTE_CYCLES,
    GROUP_DIMENSIONS,
    WORDS_PER_GROUP,
    SharedSramKWindowScheduler,
    group_word_address,
)


def test_group_word_addresses_match_tensor_layout_offsets_and_bank_rows() -> None:
    address0 = group_word_address(kv_head=2, group_index=3, word_slot=0)
    expected0 = k_beat_offset(kv_head=2, stream=0, block_slot=0, dimension=3 * GROUP_DIMENSIONS)
    assert address0.byte_offset == expected0
    assert address0.word_index == shared_word_address(expected0)
    assert address0.bank == interleaved_bank(expected0)
    assert address0.row == interleaved_row(expected0)

    address64 = group_word_address(kv_head=2, group_index=3, word_slot=BLOCKS_PER_STREAM)
    expected64 = k_beat_offset(kv_head=2, stream=1, block_slot=0, dimension=3 * GROUP_DIMENSIONS)
    assert address64.byte_offset == expected64
    assert address64.bank == interleaved_bank(expected64)
    assert address64.row == interleaved_row(expected64)

    address127 = group_word_address(kv_head=2, group_index=7, word_slot=WORDS_PER_GROUP - 1)
    expected127 = k_beat_offset(kv_head=2, stream=1, block_slot=BLOCKS_PER_STREAM - 1, dimension=7 * GROUP_DIMENSIONS)
    assert address127.byte_offset == expected127
    assert address127.word_index == shared_word_address(expected127)
    assert address127.bank == interleaved_bank(expected127)
    assert address127.row == interleaved_row(expected127)


def test_ideal_scheduler_issues_one_group_in_exactly_eight_cycles() -> None:
    result = SharedSramKWindowScheduler(response_latency=1, group_count=1).run()
    trace = result.group_traces[0]
    assert trace.request_count == WORDS_PER_GROUP
    assert trace.response_count == WORDS_PER_GROUP
    assert trace.issue_cycles == tuple(range(8))


def test_scheduler_rejects_zero_cycle_responses() -> None:
    with pytest.raises(ValueError, match="at least one cycle"):
        SharedSramKWindowScheduler(response_latency=0)


def test_latency_eight_overlaps_prefetch_with_no_steady_state_compute_stalls() -> None:
    result = SharedSramKWindowScheduler(response_latency=8).run()
    assert result.counters["steady_state_compute_stall_cycles"] == 0
    for previous, current in zip(result.group_traces, result.group_traces[1:]):
        assert current.compute_start_cycle == previous.compute_end_cycle + 1


def test_bank_backpressure_stretches_issue_window_without_breaking_order() -> None:
    def bank_ready(cycle: int, bank: int, group_index: int, word_slot: int, row: int) -> bool:
        del group_index, word_slot, row
        return not (bank == 0 and cycle < 2)

    result = SharedSramKWindowScheduler(response_latency=1, bank_ready_fn=bank_ready, group_count=1).run()
    trace = result.group_traces[0]
    assert len(trace.issue_cycles) == 10
    assert trace.issue_cycles[0] == 0
    assert trace.issue_cycles[-1] == 9
    assert result.counters["bank_wait_cycles"] >= 2


def test_latency_above_overlap_budget_introduces_compute_stalls() -> None:
    result = SharedSramKWindowScheduler(response_latency=10, group_count=3).run()
    assert result.counters["steady_state_compute_stall_cycles"] > 0
    gaps = [
        current.compute_start_cycle - previous.compute_end_cycle
        for previous, current in zip(result.group_traces, result.group_traces[1:])
    ]
    assert any(gap > 1 for gap in gaps)


def test_double_buffer_never_overwrites_a_live_window_before_release() -> None:
    result = SharedSramKWindowScheduler(response_latency=10, group_count=4).run()
    fill_start = {
        (event.group_index, event.buffer_id): event.cycle
        for event in result.events_of("fill_start")
    }
    release = {
        (event.group_index, event.buffer_id): event.cycle
        for event in result.events_of("buffer_release")
    }

    assert fill_start[(2, 0)] > release[(0, 0)]
    assert fill_start[(3, 1)] > release[(1, 1)]
    assert result.group_traces[0].compute_end_cycle - result.group_traces[0].compute_start_cycle + 1 == COMPUTE_CYCLES
