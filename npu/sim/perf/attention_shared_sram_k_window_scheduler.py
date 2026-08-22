"""Bounded reference model for the 17-bank shared-SRAM K-window scheduler.

The model covers one KV head and the eight 16-dimension K windows used by a
128-dimension Llama7B head.  Each window contains 128 shared 1024-bit words,
interleaved across 17 banks by the checked-in tensor layout contract.  The
scheduler alternates two 16 KiB buffers, issues at most one request per bank
per cycle, models a fixed response latency, and records a deterministic event
trace for overlap and stall analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from npu.sim.perf.attention_shared_sram_gqa8_tensor_layout import (
    BLOCKS_PER_STREAM,
    HEAD_DIM,
    SHARED_MACROS_PER_HOME,
    STREAMS,
    interleaved_bank,
    interleaved_row,
    k_beat_offset,
    k_prefetch_geometry,
    shared_word_address,
)


BankReadyFn = Callable[[int, int, int, int, int], bool]

GEOMETRY = k_prefetch_geometry()
GROUP_DIMENSIONS = GEOMETRY.dimension_group
GROUP_COUNT = HEAD_DIM // GROUP_DIMENSIONS
WORDS_PER_GROUP = GEOMETRY.words_per_dimension_group
COMPUTE_CYCLES = GEOMETRY.compute_cycles
BUFFER_BYTES = GEOMETRY.buffer_bytes


class SchedulerProtocolError(RuntimeError):
    """Raised when the bounded scheduler would violate the contract."""


@dataclass(frozen=True)
class KWindowWordAddress:
    kv_head: int
    group_index: int
    word_slot: int
    stream: int
    block_slot: int
    dimension_base: int
    byte_offset: int
    word_index: int
    bank: int
    row: int


@dataclass(frozen=True)
class SchedulerEvent:
    cycle: int
    kind: str
    group_index: int | None = None
    buffer_id: int | None = None
    word_slot: int | None = None
    bank: int | None = None
    row: int | None = None
    response_cycle: int | None = None
    note: str | None = None


@dataclass(frozen=True)
class GroupTrace:
    group_index: int
    buffer_id: int
    issue_cycles: tuple[int, ...]
    ready_cycle: int
    compute_start_cycle: int
    compute_end_cycle: int
    request_count: int
    response_count: int


@dataclass(frozen=True)
class SchedulerResult:
    total_cycles: int
    events: tuple[SchedulerEvent, ...]
    group_traces: tuple[GroupTrace, ...]
    counters: dict[str, int]

    def events_of(self, kind: str) -> tuple[SchedulerEvent, ...]:
        return tuple(event for event in self.events if event.kind == kind)


@dataclass
class _MutableGroupTrace:
    group_index: int
    buffer_id: int
    issue_cycles: list[int] = field(default_factory=list)
    ready_cycle: int | None = None
    compute_start_cycle: int | None = None
    compute_end_cycle: int | None = None
    request_count: int = 0
    response_count: int = 0

    def freeze(self) -> GroupTrace:
        if self.ready_cycle is None:
            raise SchedulerProtocolError(f"group {self.group_index} never became ready")
        if self.compute_start_cycle is None or self.compute_end_cycle is None:
            raise SchedulerProtocolError(f"group {self.group_index} never completed compute")
        return GroupTrace(
            group_index=self.group_index,
            buffer_id=self.buffer_id,
            issue_cycles=tuple(self.issue_cycles),
            ready_cycle=self.ready_cycle,
            compute_start_cycle=self.compute_start_cycle,
            compute_end_cycle=self.compute_end_cycle,
            request_count=self.request_count,
            response_count=self.response_count,
        )


@dataclass
class _BufferState:
    buffer_id: int
    state: str = "free"
    group_index: int | None = None
    requested: set[int] = field(default_factory=set)
    received: set[int] = field(default_factory=set)

    def clear(self) -> None:
        self.state = "free"
        self.group_index = None
        self.requested.clear()
        self.received.clear()


@dataclass(frozen=True)
class _PendingResponse:
    cycle: int
    buffer_id: int
    group_index: int
    word_slot: int
    bank: int
    row: int


def _check_kv_head(kv_head: int) -> int:
    resolved = int(kv_head)
    if resolved < 0:
        raise ValueError("kv_head must be non-negative")
    return resolved


def _check_group_index(group_index: int) -> int:
    resolved = int(group_index)
    if resolved not in range(GROUP_COUNT):
        raise ValueError(f"group_index must be in [0, {GROUP_COUNT}), got {resolved}")
    return resolved


def _check_word_slot(word_slot: int) -> int:
    resolved = int(word_slot)
    if resolved not in range(WORDS_PER_GROUP):
        raise ValueError(f"word_slot must be in [0, {WORDS_PER_GROUP}), got {resolved}")
    return resolved


def group_word_address(*, kv_head: int, group_index: int, word_slot: int) -> KWindowWordAddress:
    """Return the checked byte/bank/row address for one 1024-bit K word."""

    kv_head = _check_kv_head(kv_head)
    group_index = _check_group_index(group_index)
    word_slot = _check_word_slot(word_slot)
    stream = word_slot // BLOCKS_PER_STREAM
    block_slot = word_slot % BLOCKS_PER_STREAM
    dimension_base = group_index * GROUP_DIMENSIONS
    byte_offset = k_beat_offset(
        kv_head=kv_head,
        stream=stream,
        block_slot=block_slot,
        dimension=dimension_base,
    )
    return KWindowWordAddress(
        kv_head=kv_head,
        group_index=group_index,
        word_slot=word_slot,
        stream=stream,
        block_slot=block_slot,
        dimension_base=dimension_base,
        byte_offset=byte_offset,
        word_index=shared_word_address(byte_offset),
        bank=interleaved_bank(byte_offset),
        row=interleaved_row(byte_offset),
    )


def group_word_addresses(*, kv_head: int, group_index: int) -> tuple[KWindowWordAddress, ...]:
    return tuple(
        group_word_address(kv_head=kv_head, group_index=group_index, word_slot=word_slot)
        for word_slot in range(WORDS_PER_GROUP)
    )


def _always_ready(_cycle: int, _bank: int, _group_index: int, _word_slot: int, _row: int) -> bool:
    return True


class SharedSramKWindowScheduler:
    """Bounded double-buffered prefetch scheduler for one K head."""

    def __init__(
        self,
        *,
        kv_head: int = 0,
        response_latency: int = 1,
        bank_ready_fn: BankReadyFn | None = None,
        group_count: int = GROUP_COUNT,
    ) -> None:
        self.kv_head = _check_kv_head(kv_head)
        self.response_latency = int(response_latency)
        if self.response_latency < 1:
            raise ValueError("response_latency must be at least one cycle")
        self.group_count = int(group_count)
        if self.group_count not in range(1, GROUP_COUNT + 1):
            raise ValueError(f"group_count must be in [1, {GROUP_COUNT}], got {group_count}")
        self.bank_ready_fn = bank_ready_fn or _always_ready
        self._group_addresses = {
            group_index: group_word_addresses(kv_head=self.kv_head, group_index=group_index)
            for group_index in range(self.group_count)
        }

    def run(self) -> SchedulerResult:
        cycle = 0
        buffers = [_BufferState(buffer_id=0), _BufferState(buffer_id=1)]
        pending_responses: list[_PendingResponse] = []
        events: list[SchedulerEvent] = []
        traces = {
            group_index: _MutableGroupTrace(group_index=group_index, buffer_id=group_index % 2)
            for group_index in range(self.group_count)
        }
        counters = {
            "request_count": 0,
            "response_count": 0,
            "groups_completed": 0,
            "bank_wait_cycles": 0,
            "compute_stall_cycles": 0,
            "steady_state_compute_stall_cycles": 0,
        }

        next_group_to_fill = 0
        next_group_to_compute = 0
        active_compute: tuple[int, int, int] | None = None

        while counters["groups_completed"] < self.group_count:
            for response in tuple(sorted(pending_responses, key=lambda item: (item.cycle, item.buffer_id, item.word_slot))):
                if response.cycle != cycle:
                    continue
                pending_responses.remove(response)
                buffer_state = buffers[response.buffer_id]
                if buffer_state.state != "filling" or buffer_state.group_index != response.group_index:
                    raise SchedulerProtocolError(
                        f"response for group {response.group_index} arrived while buffer {response.buffer_id} "
                        f"held state={buffer_state.state!r} group={buffer_state.group_index!r}"
                    )
                if response.word_slot not in buffer_state.requested:
                    raise SchedulerProtocolError(
                        f"response for group {response.group_index} word {response.word_slot} had no request"
                    )
                if response.word_slot in buffer_state.received:
                    raise SchedulerProtocolError(
                        f"duplicate response for group {response.group_index} word {response.word_slot}"
                    )
                buffer_state.received.add(response.word_slot)
                trace = traces[response.group_index]
                trace.response_count += 1
                counters["response_count"] += 1
                events.append(
                    SchedulerEvent(
                        cycle=cycle,
                        kind="response",
                        group_index=response.group_index,
                        buffer_id=response.buffer_id,
                        word_slot=response.word_slot,
                        bank=response.bank,
                        row=response.row,
                    )
                )
                if len(buffer_state.received) == WORDS_PER_GROUP:
                    buffer_state.state = "ready"
                    if trace.ready_cycle is not None:
                        raise SchedulerProtocolError(f"group {response.group_index} became ready twice")
                    trace.ready_cycle = cycle
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="buffer_ready",
                            group_index=response.group_index,
                            buffer_id=response.buffer_id,
                        )
                    )

            if active_compute is None and next_group_to_compute < self.group_count:
                buffer_id = next_group_to_compute % 2
                buffer_state = buffers[buffer_id]
                if buffer_state.state == "ready" and buffer_state.group_index == next_group_to_compute:
                    active_compute = (buffer_id, next_group_to_compute, COMPUTE_CYCLES)
                    trace = traces[next_group_to_compute]
                    if trace.compute_start_cycle is not None:
                        raise SchedulerProtocolError(f"group {next_group_to_compute} started compute twice")
                    trace.compute_start_cycle = cycle
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_start",
                            group_index=next_group_to_compute,
                            buffer_id=buffer_id,
                        )
                    )
                else:
                    counters["compute_stall_cycles"] += 1
                    if next_group_to_compute > 0:
                        counters["steady_state_compute_stall_cycles"] += 1
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_stall",
                            group_index=next_group_to_compute,
                            buffer_id=buffer_id,
                        )
                    )

            fill_in_progress = any(buffer.state == "filling" for buffer in buffers)
            if next_group_to_fill < self.group_count and not fill_in_progress:
                buffer_id = next_group_to_fill % 2
                buffer_state = buffers[buffer_id]
                if buffer_state.state == "free":
                    buffer_state.state = "filling"
                    buffer_state.group_index = next_group_to_fill
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="fill_start",
                            group_index=next_group_to_fill,
                            buffer_id=buffer_id,
                        )
                    )
                    next_group_to_fill += 1

            issued_banks: set[int] = set()
            saw_blocked_word = False
            for buffer_state in sorted(buffers, key=lambda item: item.buffer_id):
                if buffer_state.state != "filling" or buffer_state.group_index is None:
                    continue
                for address in self._group_addresses[buffer_state.group_index]:
                    if address.word_slot in buffer_state.requested:
                        continue
                    if address.bank in issued_banks:
                        continue
                    if not self.bank_ready_fn(
                        cycle,
                        address.bank,
                        address.group_index,
                        address.word_slot,
                        address.row,
                    ):
                        saw_blocked_word = True
                        continue
                    buffer_state.requested.add(address.word_slot)
                    issued_banks.add(address.bank)
                    trace = traces[address.group_index]
                    trace.request_count += 1
                    if not trace.issue_cycles or trace.issue_cycles[-1] != cycle:
                        trace.issue_cycles.append(cycle)
                    counters["request_count"] += 1
                    pending_responses.append(
                        _PendingResponse(
                            cycle=cycle + self.response_latency,
                            buffer_id=buffer_state.buffer_id,
                            group_index=address.group_index,
                            word_slot=address.word_slot,
                            bank=address.bank,
                            row=address.row,
                        )
                    )
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="request",
                            group_index=address.group_index,
                            buffer_id=buffer_state.buffer_id,
                            word_slot=address.word_slot,
                            bank=address.bank,
                            row=address.row,
                            response_cycle=cycle + self.response_latency,
                        )
                    )
            if saw_blocked_word:
                counters["bank_wait_cycles"] += 1
                events.append(SchedulerEvent(cycle=cycle, kind="bank_wait"))

            if active_compute is not None:
                buffer_id, group_index, cycles_left = active_compute
                cycles_left -= 1
                if cycles_left == 0:
                    buffer_state = buffers[buffer_id]
                    if buffer_state.state != "ready" or buffer_state.group_index != group_index:
                        raise SchedulerProtocolError(
                            f"compute completed for group {group_index} while buffer {buffer_id} "
                            f"held state={buffer_state.state!r} group={buffer_state.group_index!r}"
                        )
                    trace = traces[group_index]
                    trace.compute_end_cycle = cycle
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_end",
                            group_index=group_index,
                            buffer_id=buffer_id,
                        )
                    )
                    buffer_state.clear()
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="buffer_release",
                            group_index=group_index,
                            buffer_id=buffer_id,
                        )
                    )
                    active_compute = None
                    next_group_to_compute += 1
                    counters["groups_completed"] += 1
                else:
                    active_compute = (buffer_id, group_index, cycles_left)

            cycle += 1
            if cycle > 100_000:
                raise SchedulerProtocolError("scheduler exceeded 100000 cycles")

        return SchedulerResult(
            total_cycles=cycle,
            events=tuple(events),
            group_traces=tuple(traces[group_index].freeze() for group_index in range(self.group_count)),
            counters=dict(counters),
        )
