"""Physically conservative 17-bank shared-SRAM K round scheduler reference model.

The model represents one KV head of the shared-SRAM K service after replacing
the 2x16 KiB full-window buffers with two alternating round buffers.  One
16-dimension group contains 128 checked tensor-layout words, split into
``ceil(128 / 17) == 8`` rounds.  Each round issues at most one request per bank
per cycle, accepts fixed-latency tagged responses, and exposes the completed
round to the compute side for exactly 16 cycles while the opposite buffer
prefetches the next round.
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


BankReadyFn = Callable[[int, int, int, int, int, int], bool]

GEOMETRY = k_prefetch_geometry()
BANKS = GEOMETRY.banks
WORDS_PER_GROUP = GEOMETRY.words_per_dimension_group
GROUP_DIMENSIONS = GEOMETRY.dimension_group
GROUP_COUNT = HEAD_DIM // GROUP_DIMENSIONS
COMPUTE_CYCLES = GEOMETRY.compute_cycles
WINDOW_WORDS = BANKS
ROUNDS_PER_GROUP = (WORDS_PER_GROUP + WINDOW_WORDS - 1) // WINDOW_WORDS
TOTAL_ROUNDS = GROUP_COUNT * ROUNDS_PER_GROUP
WINDOW_STORAGE_BITS = WINDOW_WORDS * 1024
TOTAL_STORAGE_BITS = 2 * WINDOW_STORAGE_BITS


class SchedulerProtocolError(RuntimeError):
    """Raised when the bounded scheduler would violate the contract."""


@dataclass(frozen=True)
class KRoundWordAddress:
    kv_head: int
    group_index: int
    round_index: int
    round_slot: int
    global_word_slot: int
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
    linear_round: int | None = None
    group_index: int | None = None
    round_index: int | None = None
    buffer_id: int | None = None
    round_slot: int | None = None
    global_word_slot: int | None = None
    bank: int | None = None
    row: int | None = None
    response_cycle: int | None = None


@dataclass(frozen=True)
class RoundTrace:
    linear_round: int
    group_index: int
    round_index: int
    valid_words: int
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
    round_traces: tuple[RoundTrace, ...]
    counters: dict[str, int]

    def events_of(self, kind: str) -> tuple[SchedulerEvent, ...]:
        return tuple(event for event in self.events if event.kind == kind)


@dataclass
class _MutableRoundTrace:
    linear_round: int
    group_index: int
    round_index: int
    valid_words: int
    buffer_id: int
    issue_cycles: list[int] = field(default_factory=list)
    ready_cycle: int | None = None
    compute_start_cycle: int | None = None
    compute_end_cycle: int | None = None
    request_count: int = 0
    response_count: int = 0

    def freeze(self) -> RoundTrace:
        if self.ready_cycle is None:
            raise SchedulerProtocolError(f"round {self.linear_round} never became ready")
        if self.compute_start_cycle is None or self.compute_end_cycle is None:
            raise SchedulerProtocolError(f"round {self.linear_round} never completed compute")
        return RoundTrace(
            linear_round=self.linear_round,
            group_index=self.group_index,
            round_index=self.round_index,
            valid_words=self.valid_words,
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
    linear_round: int | None = None
    requested: set[int] = field(default_factory=set)
    received: set[int] = field(default_factory=set)

    def clear(self) -> None:
        self.state = "free"
        self.linear_round = None
        self.requested.clear()
        self.received.clear()


@dataclass(frozen=True)
class _PendingResponse:
    cycle: int
    buffer_id: int
    linear_round: int
    round_slot: int
    bank: int
    row: int


def _check_non_negative(name: str, value: int) -> int:
    resolved = int(value)
    if resolved < 0:
        raise ValueError(f"{name} must be non-negative")
    return resolved


def _always_ready(_cycle: int, _bank: int, _group: int, _round: int, _slot: int, _row: int) -> bool:
    return True


def _round_to_group(round_linear_index: int) -> tuple[int, int]:
    resolved = _check_non_negative("round_linear_index", round_linear_index)
    return resolved // ROUNDS_PER_GROUP, resolved % ROUNDS_PER_GROUP


def round_valid_words(round_index: int, *, window_words: int = WINDOW_WORDS) -> int:
    resolved = _check_non_negative("round_index", round_index)
    if resolved >= (WORDS_PER_GROUP + window_words - 1) // window_words:
        raise ValueError("round_index is outside the configured group schedule")
    remaining = WORDS_PER_GROUP - resolved * window_words
    return min(window_words, remaining)


def round_word_address(
    *,
    kv_head: int,
    group_index: int,
    round_index: int,
    round_slot: int,
    window_words: int = WINDOW_WORDS,
) -> KRoundWordAddress:
    kv_head = _check_non_negative("kv_head", kv_head)
    group_index = _check_non_negative("group_index", group_index)
    if group_index >= GROUP_COUNT:
        raise ValueError(f"group_index must be in [0, {GROUP_COUNT}), got {group_index}")
    valid_words = round_valid_words(round_index, window_words=window_words)
    round_slot = _check_non_negative("round_slot", round_slot)
    if round_slot >= valid_words:
        raise ValueError(f"round_slot must be in [0, {valid_words}), got {round_slot}")

    global_word_slot = round_index * window_words + round_slot
    stream = global_word_slot // BLOCKS_PER_STREAM
    if stream >= STREAMS:
        raise ValueError("computed stream index exceeds checked tensor layout")
    block_slot = global_word_slot % BLOCKS_PER_STREAM
    dimension_base = group_index * GROUP_DIMENSIONS
    byte_offset = k_beat_offset(
        kv_head=kv_head,
        stream=stream,
        block_slot=block_slot,
        dimension=dimension_base,
    )
    return KRoundWordAddress(
        kv_head=kv_head,
        group_index=group_index,
        round_index=round_index,
        round_slot=round_slot,
        global_word_slot=global_word_slot,
        stream=stream,
        block_slot=block_slot,
        dimension_base=dimension_base,
        byte_offset=byte_offset,
        word_index=shared_word_address(byte_offset),
        bank=interleaved_bank(byte_offset),
        row=interleaved_row(byte_offset),
    )


def round_word_addresses(
    *,
    kv_head: int,
    group_index: int,
    round_index: int,
    window_words: int = WINDOW_WORDS,
) -> tuple[KRoundWordAddress, ...]:
    addresses = tuple(
        round_word_address(
            kv_head=kv_head,
            group_index=group_index,
            round_index=round_index,
            round_slot=round_slot,
            window_words=window_words,
        )
        for round_slot in range(round_valid_words(round_index, window_words=window_words))
    )
    seen_banks = {address.bank for address in addresses}
    if len(seen_banks) != len(addresses):
        raise ValueError(
            "configured round contains duplicate bank targets; this model currently requires window_words <= banks"
        )
    return addresses


class SharedSramKRoundScheduler:
    """Bounded double-buffered round scheduler for one shared-SRAM K head."""

    def __init__(
        self,
        *,
        kv_head: int = 0,
        response_latency: int = 1,
        bank_ready_fn: BankReadyFn | None = None,
        group_count: int = GROUP_COUNT,
        window_words: int = WINDOW_WORDS,
        banks: int = BANKS,
    ) -> None:
        self.kv_head = _check_non_negative("kv_head", kv_head)
        self.response_latency = int(response_latency)
        if self.response_latency < 1:
            raise ValueError("response_latency must be at least one cycle")
        self.group_count = int(group_count)
        if self.group_count not in range(1, GROUP_COUNT + 1):
            raise ValueError(f"group_count must be in [1, {GROUP_COUNT}], got {group_count}")
        self.banks = int(banks)
        if self.banks <= 0:
            raise ValueError("banks must be positive")
        self.window_words = int(window_words)
        if self.window_words <= 0:
            raise ValueError("window_words must be positive")
        if self.window_words > self.banks:
            raise ValueError("window_words must not exceed banks in the current reference model")
        self.rounds_per_group = (WORDS_PER_GROUP + self.window_words - 1) // self.window_words
        self.total_rounds = self.group_count * self.rounds_per_group
        self.bank_ready_fn = bank_ready_fn or _always_ready

        self._round_addresses: dict[tuple[int, int], tuple[KRoundWordAddress, ...]] = {}
        for group_index in range(self.group_count):
            for round_index in range(self.rounds_per_group):
                self._round_addresses[(group_index, round_index)] = round_word_addresses(
                    kv_head=self.kv_head,
                    group_index=group_index,
                    round_index=round_index,
                    window_words=self.window_words,
                )

    def run(self) -> SchedulerResult:
        cycle = 0
        buffers = [_BufferState(buffer_id=0), _BufferState(buffer_id=1)]
        pending_responses: list[_PendingResponse] = []
        events: list[SchedulerEvent] = []
        traces = {
            linear_round: _MutableRoundTrace(
                linear_round=linear_round,
                group_index=_round_to_group(linear_round)[0],
                round_index=_round_to_group(linear_round)[1],
                valid_words=round_valid_words(_round_to_group(linear_round)[1], window_words=self.window_words),
                buffer_id=linear_round % 2,
            )
            for linear_round in range(self.total_rounds)
        }
        counters = {
            "request_count": 0,
            "response_count": 0,
            "rounds_ready": 0,
            "rounds_completed": 0,
            "compute_cycles": 0,
            "bank_wait_cycles": 0,
            "compute_stall_cycles": 0,
            "steady_state_compute_stall_cycles": 0,
        }

        next_round_to_fill = 0
        next_round_to_compute = 0
        active_compute: tuple[int, int, int] | None = None

        while counters["rounds_completed"] < self.total_rounds:
            for response in tuple(sorted(pending_responses, key=lambda item: (item.cycle, item.buffer_id, item.round_slot))):
                if response.cycle != cycle:
                    continue
                pending_responses.remove(response)
                buffer_state = buffers[response.buffer_id]
                if buffer_state.state != "filling" or buffer_state.linear_round != response.linear_round:
                    raise SchedulerProtocolError(
                        f"response for round {response.linear_round} arrived while buffer {response.buffer_id} "
                        f"held state={buffer_state.state!r} round={buffer_state.linear_round!r}"
                    )
                if response.round_slot not in buffer_state.requested:
                    raise SchedulerProtocolError(
                        f"response for round {response.linear_round} slot {response.round_slot} had no request"
                    )
                if response.round_slot in buffer_state.received:
                    raise SchedulerProtocolError(
                        f"duplicate response for round {response.linear_round} slot {response.round_slot}"
                    )
                buffer_state.received.add(response.round_slot)
                trace = traces[response.linear_round]
                trace.response_count += 1
                counters["response_count"] += 1
                events.append(
                    SchedulerEvent(
                        cycle=cycle,
                        kind="response",
                        linear_round=response.linear_round,
                        group_index=trace.group_index,
                        round_index=trace.round_index,
                        buffer_id=response.buffer_id,
                        round_slot=response.round_slot,
                        bank=response.bank,
                        row=response.row,
                    )
                )
                if len(buffer_state.received) == trace.valid_words:
                    if trace.ready_cycle is not None:
                        raise SchedulerProtocolError(f"round {response.linear_round} became ready twice")
                    trace.ready_cycle = cycle
                    buffer_state.state = "ready"
                    counters["rounds_ready"] += 1
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="round_ready",
                            linear_round=response.linear_round,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=response.buffer_id,
                        )
                    )

            if active_compute is None and next_round_to_compute < self.total_rounds:
                buffer_id = next_round_to_compute % 2
                buffer_state = buffers[buffer_id]
                trace = traces[next_round_to_compute]
                if buffer_state.state == "ready" and buffer_state.linear_round == next_round_to_compute:
                    trace.compute_start_cycle = cycle
                    active_compute = (buffer_id, next_round_to_compute, COMPUTE_CYCLES)
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_start",
                            linear_round=next_round_to_compute,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_id,
                        )
                    )
                else:
                    counters["compute_stall_cycles"] += 1
                    if next_round_to_compute > 0:
                        counters["steady_state_compute_stall_cycles"] += 1
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_stall",
                            linear_round=next_round_to_compute,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_id,
                        )
                    )

            if next_round_to_fill < self.total_rounds:
                buffer_id = next_round_to_fill % 2
                buffer_state = buffers[buffer_id]
                if buffer_state.state == "free":
                    trace = traces[next_round_to_fill]
                    buffer_state.state = "filling"
                    buffer_state.linear_round = next_round_to_fill
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="fill_start",
                            linear_round=next_round_to_fill,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_id,
                        )
                    )
                    next_round_to_fill += 1

            issued_banks: set[int] = set()
            saw_blocked_word = False
            for buffer_state in sorted(buffers, key=lambda item: item.buffer_id):
                if buffer_state.state != "filling" or buffer_state.linear_round is None:
                    continue
                trace = traces[buffer_state.linear_round]
                addresses = self._round_addresses[(trace.group_index, trace.round_index)]
                for address in addresses:
                    if address.round_slot in buffer_state.requested:
                        continue
                    if address.bank in issued_banks:
                        continue
                    if not self.bank_ready_fn(
                        cycle,
                        address.bank,
                        address.group_index,
                        address.round_index,
                        address.round_slot,
                        address.row,
                    ):
                        saw_blocked_word = True
                        continue
                    buffer_state.requested.add(address.round_slot)
                    issued_banks.add(address.bank)
                    if not trace.issue_cycles or trace.issue_cycles[-1] != cycle:
                        trace.issue_cycles.append(cycle)
                    trace.request_count += 1
                    counters["request_count"] += 1
                    pending_responses.append(
                        _PendingResponse(
                            cycle=cycle + self.response_latency,
                            buffer_id=buffer_state.buffer_id,
                            linear_round=buffer_state.linear_round,
                            round_slot=address.round_slot,
                            bank=address.bank,
                            row=address.row,
                        )
                    )
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="request",
                            linear_round=buffer_state.linear_round,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_state.buffer_id,
                            round_slot=address.round_slot,
                            global_word_slot=address.global_word_slot,
                            bank=address.bank,
                            row=address.row,
                            response_cycle=cycle + self.response_latency,
                        )
                    )
            if saw_blocked_word:
                counters["bank_wait_cycles"] += 1
                events.append(SchedulerEvent(cycle=cycle, kind="bank_wait"))

            if active_compute is not None:
                buffer_id, linear_round, cycles_left = active_compute
                counters["compute_cycles"] += 1
                cycles_left -= 1
                if cycles_left == 0:
                    buffer_state = buffers[buffer_id]
                    if buffer_state.state != "ready" or buffer_state.linear_round != linear_round:
                        raise SchedulerProtocolError(
                            f"compute completed for round {linear_round} while buffer {buffer_id} "
                            f"held state={buffer_state.state!r} round={buffer_state.linear_round!r}"
                        )
                    trace = traces[linear_round]
                    trace.compute_end_cycle = cycle
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="compute_end",
                            linear_round=linear_round,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_id,
                        )
                    )
                    buffer_state.clear()
                    events.append(
                        SchedulerEvent(
                            cycle=cycle,
                            kind="buffer_release",
                            linear_round=linear_round,
                            group_index=trace.group_index,
                            round_index=trace.round_index,
                            buffer_id=buffer_id,
                        )
                    )
                    active_compute = None
                    next_round_to_compute += 1
                    counters["rounds_completed"] += 1
                else:
                    active_compute = (buffer_id, linear_round, cycles_left)

            cycle += 1
            if cycle > 100_000:
                raise SchedulerProtocolError("scheduler exceeded 100000 cycles")

        return SchedulerResult(
            total_cycles=cycle,
            events=tuple(events),
            round_traces=tuple(traces[index].freeze() for index in range(self.total_rounds)),
            counters=dict(counters),
        )
