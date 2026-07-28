"""Exact streamed partial-state reference for score32 online reduction."""

from __future__ import annotations

from dataclasses import dataclass
import math
import operator
from typing import Iterable

from npu.sim.perf.attention_online import (
    EXP_SUM_BITS,
    FINAL_VALUE_BITS,
    MERGE_SCALE_BITS,
    SCORE_BITS,
    WEIGHTED_NUMERATOR_BITS,
    AttentionOnlineStats,
    finalize_value,
    merge_stats,
    two_pass_stats,
)
from npu.sim.perf.attention_separated import (
    EXP_BUCKET_SHIFT,
    MAX_EXP_BUCKET,
    WEIGHT_SCALE,
    _exp_lut,
)

HEAD_ID_BITS = 5
SLICE_LANES = 8
VALUE_SLICES = 16
SLICE_INDEX_BITS = (VALUE_SLICES - 1).bit_length()
PARTIAL_PAYLOAD_BITS = SLICE_LANES * WEIGHTED_NUMERATOR_BITS
PARTIAL_LINK_BITS = PARTIAL_PAYLOAD_BITS + 16 + HEAD_ID_BITS + SCORE_BITS + EXP_SUM_BITS + SLICE_INDEX_BITS + 1
EXACT_STATE_BITS_PER_HEAD = (VALUE_SLICES * PARTIAL_PAYLOAD_BITS) + SCORE_BITS + EXP_SUM_BITS
EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS = (EXACT_STATE_BITS_PER_HEAD * 32) // 8
LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS = (PARTIAL_LINK_BITS * VALUE_SLICES * 32) // 8
FINAL_PAYLOAD_BITS = SLICE_LANES * FINAL_VALUE_BITS
FINAL_LINK_BITS = FINAL_PAYLOAD_BITS + 16 + HEAD_ID_BITS + SLICE_INDEX_BITS + 1
MERGE_SCALE = (1 << MERGE_SCALE_BITS) - 1


def _clamp_signed(value: int, bits: int) -> int:
    lower = -(1 << (bits - 1))
    upper = (1 << (bits - 1)) - 1
    return max(lower, min(upper, int(value)))


def _clamp_unsigned(value: int, bits: int) -> int:
    return max(0, min((1 << bits) - 1, int(value)))


def _round_div_signed(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    magnitude = (abs(int(numerator)) + denominator // 2) // denominator
    return -magnitude if numerator < 0 else magnitude


def _bucket(delta: int) -> int:
    return max(0, (int(delta) + (1 << (EXP_BUCKET_SHIFT - 1))) >> EXP_BUCKET_SHIFT)


def _online_exp_lut(bucket: int, *, output_scale: int = WEIGHT_SCALE) -> int:
    if bucket > MAX_EXP_BUCKET:
        return 0
    if output_scale == WEIGHT_SCALE:
        return _exp_lut(bucket)
    step = float(1 << EXP_BUCKET_SHIFT) / float(1 << 28)
    return max(1, int(math.exp(-(bucket * step)) * output_scale + 0.5))


def _scale_unsigned(value: int, scale: int, *, scale_one: int) -> int:
    return _clamp_unsigned((int(value) * int(scale) + scale_one // 2) // scale_one, EXP_SUM_BITS)


def _scale_signed(value: int, scale: int, *, scale_one: int) -> int:
    return _clamp_signed(_round_div_signed(int(value) * int(scale), scale_one), WEIGHTED_NUMERATOR_BITS)


@dataclass(frozen=True)
class ExactPartialBeat:
    command_id: int
    head_id: int
    slice_index: int
    last: bool
    max_score: int
    exp_sum: int
    numerators: tuple[int, ...]

    def __post_init__(self) -> None:
        if not 0 <= int(self.command_id) < (1 << 16):
            raise ValueError("command_id must fit unsigned 16 bits")
        if not 0 <= int(self.head_id) < (1 << HEAD_ID_BITS):
            raise ValueError(f"head_id must fit unsigned {HEAD_ID_BITS} bits")
        if not 0 <= int(self.slice_index) < VALUE_SLICES:
            raise ValueError(f"slice_index must be in [0, {VALUE_SLICES})")
        if bool(self.last) != (int(self.slice_index) == VALUE_SLICES - 1):
            raise ValueError("last must match the terminal slice index")
        if not -(1 << (SCORE_BITS - 1)) <= int(self.max_score) < (1 << (SCORE_BITS - 1)):
            raise ValueError(f"max_score must fit signed {SCORE_BITS} bits")
        if not 0 <= int(self.exp_sum) < (1 << EXP_SUM_BITS):
            raise ValueError(f"exp_sum must fit unsigned {EXP_SUM_BITS} bits")
        numerators = tuple(int(value) for value in self.numerators)
        if len(numerators) != SLICE_LANES:
            raise ValueError(f"numerators must contain {SLICE_LANES} lanes")
        limit = 1 << (WEIGHTED_NUMERATOR_BITS - 1)
        if any(not -limit <= value < limit for value in numerators):
            raise ValueError(f"numerators must fit signed {WEIGHTED_NUMERATOR_BITS} bits")

    def as_stats(self) -> AttentionOnlineStats:
        return AttentionOnlineStats(
            max_score=int(self.max_score),
            exp_sum=int(self.exp_sum),
            weighted_numerator=tuple(int(value) for value in self.numerators),
            block_count=1,
        )


@dataclass(frozen=True)
class ExactFinalizedBeat:
    command_id: int
    head_id: int
    slice_index: int
    last: bool
    values: tuple[int, ...]

    def __post_init__(self) -> None:
        if not 0 <= int(self.command_id) < (1 << 16):
            raise ValueError("command_id must fit unsigned 16 bits")
        if not 0 <= int(self.head_id) < (1 << HEAD_ID_BITS):
            raise ValueError(f"head_id must fit unsigned {HEAD_ID_BITS} bits")
        if not 0 <= int(self.slice_index) < VALUE_SLICES:
            raise ValueError(f"slice_index must be in [0, {VALUE_SLICES})")
        if bool(self.last) != (int(self.slice_index) == VALUE_SLICES - 1):
            raise ValueError("last must match the terminal slice index")
        values = tuple(int(value) for value in self.values)
        if len(values) != SLICE_LANES:
            raise ValueError(f"values must contain {SLICE_LANES} lanes")
        limit = 1 << (FINAL_VALUE_BITS - 1)
        if any(not -limit <= value < limit for value in values):
            raise ValueError(f"values must fit signed {FINAL_VALUE_BITS} bits")


def pack_numerators(values: Iterable[int]) -> int:
    mask = (1 << WEIGHTED_NUMERATOR_BITS) - 1
    lanes = tuple(int(value) for value in values)
    if len(lanes) != SLICE_LANES:
        raise ValueError(f"expected {SLICE_LANES} lanes")
    return sum((value & mask) << (index * WEIGHTED_NUMERATOR_BITS) for index, value in enumerate(lanes))


def unpack_numerators(word: int) -> tuple[int, ...]:
    mask = (1 << WEIGHTED_NUMERATOR_BITS) - 1
    values: list[int] = []
    for index in range(SLICE_LANES):
        raw = (int(word) >> (index * WEIGHTED_NUMERATOR_BITS)) & mask
        if raw & (1 << (WEIGHTED_NUMERATOR_BITS - 1)):
            raw -= 1 << WEIGHTED_NUMERATOR_BITS
        values.append(raw)
    return tuple(values)


def pack_final_values(values: Iterable[int]) -> int:
    mask = (1 << FINAL_VALUE_BITS) - 1
    lanes = tuple(int(value) for value in values)
    if len(lanes) != SLICE_LANES:
        raise ValueError(f"expected {SLICE_LANES} lanes")
    return sum((value & mask) << (index * FINAL_VALUE_BITS) for index, value in enumerate(lanes))


def unpack_final_values(word: int) -> tuple[int, ...]:
    mask = (1 << FINAL_VALUE_BITS) - 1
    values: list[int] = []
    for index in range(SLICE_LANES):
        raw = (int(word) >> (index * FINAL_VALUE_BITS)) & mask
        if raw & (1 << (FINAL_VALUE_BITS - 1)):
            raw -= 1 << FINAL_VALUE_BITS
        values.append(raw)
    return tuple(values)


def partial_stream_from_blocks(
    *,
    command_id: int,
    head_id: int,
    score_rows: Iterable[Iterable[int]],
    value_blocks: Iterable[Iterable[Iterable[Iterable[int]]]],
) -> tuple[ExactPartialBeat, ...]:
    score_list = [tuple(int(value) for value in row) for row in score_rows]
    value_list = [
        tuple(
            tuple(tuple(int(value) for value in lane_row) for lane_row in value_slice)
            for value_slice in block
        )
        for block in value_blocks
    ]
    if not score_list or len(score_list) != len(value_list):
        raise ValueError("score_rows and value_blocks must contain the same nonzero block count")
    if any(len(block) != VALUE_SLICES for block in value_list):
        raise ValueError(f"each block must contain {VALUE_SLICES} value slices")
    beats: list[ExactPartialBeat] = []
    for slice_index in range(VALUE_SLICES):
        stats = two_pass_stats(score_list, [block[slice_index] for block in value_list])
        beats.append(
            ExactPartialBeat(
                command_id=int(command_id) & 0xFFFF,
                head_id=int(head_id) & ((1 << HEAD_ID_BITS) - 1),
                slice_index=slice_index,
                last=slice_index == VALUE_SLICES - 1,
                max_score=stats.max_score,
                exp_sum=stats.exp_sum,
                numerators=stats.weighted_numerator,
            )
        )
    return tuple(beats)


def finalize_partial_beat(beat: ExactPartialBeat) -> ExactFinalizedBeat:
    return ExactFinalizedBeat(
        command_id=beat.command_id,
        head_id=beat.head_id,
        slice_index=beat.slice_index,
        last=beat.last,
        values=tuple(int(value) for value in finalize_value(beat.as_stats())),
    )


def finalize_partial_beats(stream: Iterable[ExactPartialBeat]) -> tuple[ExactFinalizedBeat, ...]:
    return tuple(finalize_partial_beat(beat) for beat in stream)


def merge_partial_beats(left: ExactPartialBeat, right: ExactPartialBeat) -> ExactPartialBeat:
    if left.command_id != right.command_id:
        raise ValueError("command_id mismatch across partial beats")
    if left.head_id != right.head_id:
        raise ValueError("head_id mismatch across partial beats")
    if left.slice_index != right.slice_index or left.last != right.last:
        raise ValueError("slice sequencing mismatch across partial beats")
    maximum = max(int(left.max_score), int(right.max_score))
    left_scale = _online_exp_lut(_bucket(maximum - int(left.max_score)), output_scale=MERGE_SCALE)
    right_scale = _online_exp_lut(_bucket(maximum - int(right.max_score)), output_scale=MERGE_SCALE)
    numerators = tuple(
        _scale_signed(left.numerators[lane], left_scale, scale_one=MERGE_SCALE)
        + _scale_signed(right.numerators[lane], right_scale, scale_one=MERGE_SCALE)
        for lane in range(SLICE_LANES)
    )
    numerators = tuple(_clamp_signed(value, WEIGHTED_NUMERATOR_BITS) for value in numerators)
    exp_sum = _scale_unsigned(left.exp_sum, left_scale, scale_one=MERGE_SCALE) + _scale_unsigned(
        right.exp_sum, right_scale, scale_one=MERGE_SCALE
    )
    return ExactPartialBeat(
        command_id=left.command_id,
        head_id=left.head_id,
        slice_index=left.slice_index,
        last=left.last,
        max_score=maximum,
        exp_sum=_clamp_unsigned(exp_sum, EXP_SUM_BITS),
        numerators=numerators,
    )


def finalize_partial_stream(stream: Iterable[ExactPartialBeat]) -> tuple[tuple[int, ...], ...]:
    return tuple(finalize_value(beat.as_stats()) for beat in stream)


def simulate_exact_finalizer(
    stream: Iterable[ExactPartialBeat],
    *,
    divider_lanes: int,
    output_ready_pattern: Iterable[bool] | None = None,
) -> dict[str, object]:
    lanes = int(divider_lanes)
    if lanes not in {1, 2, 4, 8}:
        raise ValueError("divider_lanes must be one of 1, 2, 4, 8")
    groups = SLICE_LANES // lanes
    divide_cycles = 57
    ready_pattern = tuple(output_ready_pattern) if output_ready_pattern is not None else ()
    partials = tuple(stream)
    finalized = tuple(finalize_partial_beat(beat) for beat in partials)
    accept_events: list[dict[str, int]] = []
    result_events: list[dict[str, int | bool]] = []
    cycle = 0
    for index, beat in enumerate(finalized):
        accept_events.append({"index": index, "cycle": cycle})
        cycle += finalizer_output_latency_cycles(lanes)
        if ready_pattern:
            while not ready_pattern[cycle % len(ready_pattern)]:
                cycle += 1
        result_events.append(
            {
                "index": index,
                "cycle": cycle,
                "command_id": beat.command_id,
                "head_id": beat.head_id,
                "slice": beat.slice_index,
                "last": beat.last,
            }
        )
        cycle += 1
    return {
        "divider_lanes": lanes,
        "groups_per_beat": groups,
        "divide_cycles_per_group": divide_cycles,
        "accept_events": accept_events,
        "result_events": result_events,
        "accepted_count": len(accept_events),
        "completed_count": len(result_events),
        "first_output_cycle": result_events[0]["cycle"] if result_events else -1,
        "last_output_cycle": result_events[-1]["cycle"] if result_events else -1,
        "drain_cycles": cycle,
    }


def finalizer_cycles_per_beat(divider_lanes: int) -> int:
    lanes = int(divider_lanes)
    if lanes not in {1, 2, 4, 8}:
        raise ValueError("divider_lanes must be one of 1, 2, 4, 8")
    return (SLICE_LANES // lanes) * 57


def finalizer_output_latency_cycles(divider_lanes: int) -> int:
    return finalizer_cycles_per_beat(divider_lanes) + 1


def finalizer_accept_interval_cycles(divider_lanes: int) -> int:
    return finalizer_cycles_per_beat(divider_lanes) + 2


def _require_int_arg(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        return operator.index(value)
    except TypeError as exc:
        raise ValueError(f"{label} must be an integer") from exc


def exact_banked_finalized_tree_full_wave_saturated_service(
    *,
    clusters: int,
    heads: int = 32,
    divider_lanes: int = 8,
    finalizer_banks: int = 1,
) -> dict[str, int | float | str | bool]:
    cluster_count = _require_int_arg(clusters, "clusters")
    head_count = _require_int_arg(heads, "heads")
    lanes = _require_int_arg(divider_lanes, "divider_lanes")
    banks = _require_int_arg(finalizer_banks, "finalizer_banks")
    if cluster_count < 2 or cluster_count > 16 or (cluster_count & (cluster_count - 1)):
        raise ValueError("clusters must be a power of two in [2, 16]")
    if head_count < 1 or head_count > 32:
        raise ValueError("heads must be in [1, 32]")
    if lanes not in {1, 2, 4, 8}:
        raise ValueError("divider_lanes must be one of 1, 2, 4, 8")
    if banks < 1 or banks > 64:
        raise ValueError("finalizer_banks must be in [1, 64]")

    tree_stages = int(math.log2(cluster_count))
    root_beats = head_count * VALUE_SLICES
    divider_iterations = 57
    output_latency_cycles = finalizer_output_latency_cycles(lanes)
    accept_interval_cycles = finalizer_accept_interval_cycles(lanes)
    first_output_cycle = tree_stages + output_latency_cycles
    wrap_shortage_cycles = max(0, accept_interval_cycles - banks)
    wrap_count = (root_beats - 1) // banks if root_beats > 1 else 0
    dispatch_stall_cycles = wrap_count * wrap_shortage_cycles
    interval_cycles = (root_beats - 1) + dispatch_stall_cycles if root_beats > 1 else 0
    last_output_cycle = first_output_cycle + interval_cycles
    drain_cycles = last_output_cycle + 1
    return {
        "service_mode": "full_wave_saturated_no_output_stall",
        "clusters": cluster_count,
        "tree_stages": tree_stages,
        "heads": head_count,
        "root_beats": root_beats,
        "divider_lanes": lanes,
        "finalizer_banks": banks,
        "divider_iterations_per_group": divider_iterations,
        "per_bank_output_latency_cycles": output_latency_cycles,
        "per_bank_accept_interval_cycles": accept_interval_cycles,
        "wrap_shortage_cycles_per_bank_reuse": wrap_shortage_cycles,
        "wrap_event_count": wrap_count,
        "dispatch_stall_cycles": dispatch_stall_cycles,
        "first_output_cycle": first_output_cycle,
        "last_output_cycle": last_output_cycle,
        "interval_cycles": interval_cycles,
        "cycles_per_beat": interval_cycles / float(max(1, root_beats - 1)),
        "drain_cycles": drain_cycles,
        "exact_no_stall_full_wave_service": dispatch_stall_cycles == 0,
    }


def merge_partial_streams(
    left: Iterable[ExactPartialBeat],
    right: Iterable[ExactPartialBeat],
) -> tuple[ExactPartialBeat, ...]:
    left_beats = tuple(left)
    right_beats = tuple(right)
    if len(left_beats) != VALUE_SLICES or len(right_beats) != VALUE_SLICES:
        raise ValueError(f"expected exactly {VALUE_SLICES} beats per partial stream")
    return tuple(merge_partial_beats(left_beats[index], right_beats[index]) for index in range(VALUE_SLICES))


def merge_balanced_partial_streams(streams: Iterable[Iterable[ExactPartialBeat]]) -> tuple[ExactPartialBeat, ...]:
    level = [tuple(stream) for stream in streams]
    if not level:
        raise ValueError("expected at least one partial stream")
    if len(level) & (len(level) - 1):
        raise ValueError("stream count must be a power of two")
    expected_beats = len(level[0])
    if expected_beats == 0:
        raise ValueError("partial streams must be non-empty")
    if any(len(stream) != expected_beats for stream in level):
        raise ValueError("all partial streams must contain the same beat count")
    while len(level) > 1:
        next_level: list[tuple[ExactPartialBeat, ...]] = []
        for index in range(0, len(level), 2):
            next_level.append(
                tuple(
                    merge_partial_beats(level[index][beat_index], level[index + 1][beat_index])
                    for beat_index in range(expected_beats)
                )
            )
        level = next_level
    return level[0]


def merge_partial_streams_via_local_normalization(
    left: Iterable[ExactPartialBeat],
    right: Iterable[ExactPartialBeat],
) -> tuple[ExactPartialBeat, ...]:
    def _requantized_stats(beat: ExactPartialBeat) -> AttentionOnlineStats:
        finalized = finalize_value(beat.as_stats())
        numerators = tuple(
            _round_div_signed(int(value) * int(beat.exp_sum), WEIGHT_SCALE) for value in finalized
        )
        return AttentionOnlineStats(
            max_score=beat.max_score,
            exp_sum=beat.exp_sum,
            weighted_numerator=numerators,
            block_count=1,
        )

    merged: list[ExactPartialBeat] = []
    for left_beat, right_beat in zip(tuple(left), tuple(right)):
        approx = merge_stats(_requantized_stats(left_beat), _requantized_stats(right_beat))
        merged.append(
            ExactPartialBeat(
                command_id=left_beat.command_id,
                head_id=left_beat.head_id,
                slice_index=left_beat.slice_index,
                last=left_beat.last,
                max_score=approx.max_score,
                exp_sum=approx.exp_sum,
                numerators=approx.weighted_numerator,
            )
        )
    return tuple(merged)


def normalized_merge_guard_case() -> tuple[tuple[ExactPartialBeat, ...], tuple[ExactPartialBeat, ...]]:
    score_rows_left = (
        (41, -17, 9, -33, 15, -1, 22, -45),
        (37, -20, 11, -28, 19, -4, 18, -39),
    )
    score_rows_right = (
        (5, -4, 3, -2, 1, 0, -1, 2),
        (7, -6, 5, -4, 3, -2, 1, 0),
    )

    def _value_block(seed: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
        return tuple(
            tuple(
                tuple((((seed * 13) + slice_index * 17 + row * 11 + lane * 7) % 255) - 127 for lane in range(8))
                for row in range(8)
            )
            for slice_index in range(VALUE_SLICES)
        )

    left = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=7,
        score_rows=score_rows_left,
        value_blocks=(_value_block(3), _value_block(9)),
    )
    right = partial_stream_from_blocks(
        command_id=0x4A21,
        head_id=7,
        score_rows=score_rows_right,
        value_blocks=(_value_block(21), _value_block(27)),
    )
    exact = merge_partial_streams(left, right)
    invalid = merge_partial_streams_via_local_normalization(left, right)
    if finalize_partial_stream(exact) == finalize_partial_stream(invalid):
        raise RuntimeError("failed to materialize an adversarial normalized-merge mismatch")
    return left, right


def exact_partial_tree_service_manifest(*, clusters: int, heads: int = 32) -> dict[str, int | bool | str]:
    cluster_count = int(clusters)
    head_count = int(heads)
    if cluster_count < 2 or cluster_count > 16 or (cluster_count & (cluster_count - 1)):
        raise ValueError("clusters must be a power of two in [2, 16]")
    if head_count < 1:
        raise ValueError("heads must be positive")
    stages = int(math.log2(cluster_count))
    nodes = cluster_count - 1
    exact_state_bytes_per_cluster = (EXACT_STATE_BITS_PER_HEAD * head_count) // 8
    leaf_stream_bytes_per_cluster = (PARTIAL_LINK_BITS * VALUE_SLICES * head_count) // 8
    return {
        "clusters": cluster_count,
        "heads": head_count,
        "radix": 2,
        "tree_stages": stages,
        "tree_nodes": nodes,
        "value_slices": VALUE_SLICES,
        "slice_lanes": SLICE_LANES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "exact_state_bytes_per_cluster": exact_state_bytes_per_cluster,
        "leaf_stream_bytes_per_cluster": leaf_stream_bytes_per_cluster,
        "total_leaf_stream_bytes": leaf_stream_bytes_per_cluster * cluster_count,
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": False,
        "finalizer_boundary": "next_phase",
        "future_area_sensitivity": "folded_or_radix4_tree",
    }


def exact_finalized_tree_service_manifest(
    *,
    clusters: int,
    heads: int = 32,
    divider_lanes: int = 8,
) -> dict[str, int | bool | str]:
    manifest = dict(exact_partial_tree_service_manifest(clusters=clusters, heads=heads))
    lanes = int(divider_lanes)
    manifest.update(
        {
            "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
            "final_link_bits_per_beat": FINAL_LINK_BITS,
            "divider_lanes": lanes,
            "physical_divider_lanes": lanes,
            "divider_groups_per_beat": SLICE_LANES // lanes,
            "divider_iterations_per_group": 57,
            "divider_cycles_per_beat": finalizer_cycles_per_beat(lanes),
            "per_bank_output_latency_cycles": finalizer_output_latency_cycles(lanes),
            "per_bank_accept_interval_cycles": finalizer_accept_interval_cycles(lanes),
            "root_output_bytes": ((FINAL_LINK_BITS * VALUE_SLICES * int(heads)) + 7) // 8,
            "direct_328bit_links_unclosed": True,
            "final_divider_embodied": True,
            "finalizer_boundary": "embodied",
            "future_area_sensitivity": "folded_tree_or_lane_count",
        }
    )
    return manifest


def simulate_exact_banked_finalizer(
    stream: Iterable[ExactPartialBeat],
    *,
    divider_lanes: int,
    finalizer_banks: int,
    output_ready_pattern: Iterable[bool] | None = None,
) -> dict[str, object]:
    lanes = int(divider_lanes)
    banks = int(finalizer_banks)
    if lanes not in {1, 2, 4, 8}:
        raise ValueError("divider_lanes must be one of 1, 2, 4, 8")
    if banks < 1 or banks > 64:
        raise ValueError("finalizer_banks must be in [1, 64]")
    beats = tuple(stream)
    finalized = tuple(finalize_partial_beat(beat) for beat in beats)
    ready_pattern = tuple(bool(value) for value in output_ready_pattern) if output_ready_pattern is not None else ()
    divide_cycles = finalizer_cycles_per_beat(lanes)
    output_latency_cycles = finalizer_output_latency_cycles(lanes)
    next_issue_index = 0
    dispatch_bank = 0
    cycle = 0
    order_fifo: list[int] = []
    high_watermark = 0
    dispatch_stall_cycles = 0
    bank_state = [
        {
            "busy_cycles_left": 0,
            "output_pending": False,
            "output_index": -1,
            "accepted_count": 0,
            "completed_count": 0,
        }
        for _ in range(banks)
    ]
    accept_events: list[dict[str, int]] = []
    result_events: list[dict[str, int | bool]] = []

    while next_issue_index < len(finalized) or order_fifo:
        head_bank = order_fifo[0] if order_fifo else -1
        out_ready = ready_pattern[cycle % len(ready_pattern)] if ready_pattern else True
        dequeue_fire = bool(order_fifo and bank_state[head_bank]["output_pending"] and out_ready)
        enqueue_ready = (len(order_fifo) < banks) or dequeue_fire
        selected_bank_ready = (
            next_issue_index < len(finalized)
            and bank_state[dispatch_bank]["busy_cycles_left"] == 0
            and not bank_state[dispatch_bank]["output_pending"]
        )
        enqueue_fire = bool(next_issue_index < len(finalized) and enqueue_ready and selected_bank_ready)
        if next_issue_index < len(finalized) and not enqueue_fire:
            dispatch_stall_cycles += 1

        if dequeue_fire:
            output_index = int(bank_state[head_bank]["output_index"])
            beat = finalized[output_index]
            result_events.append(
                {
                    "index": output_index,
                    "cycle": cycle,
                    "bank": head_bank,
                    "command_id": beat.command_id,
                    "head_id": beat.head_id,
                    "slice": beat.slice_index,
                    "last": beat.last,
                }
            )

        if enqueue_fire:
            bank_state[dispatch_bank]["busy_cycles_left"] = output_latency_cycles
            bank_state[dispatch_bank]["output_pending"] = False
            bank_state[dispatch_bank]["output_index"] = next_issue_index
            bank_state[dispatch_bank]["accepted_count"] += 1
            accept_events.append({"index": next_issue_index, "cycle": cycle, "bank": dispatch_bank})
            order_fifo.append(dispatch_bank)
            high_watermark = max(high_watermark, len(order_fifo))
            next_issue_index += 1
            dispatch_bank = (dispatch_bank + 1) % banks

        if dequeue_fire:
            bank_state[head_bank]["output_pending"] = False
            bank_state[head_bank]["output_index"] = -1
            bank_state[head_bank]["completed_count"] += 1
            order_fifo.pop(0)

        for state in bank_state:
            if int(state["busy_cycles_left"]) > 0:
                state["busy_cycles_left"] = int(state["busy_cycles_left"]) - 1
                if int(state["busy_cycles_left"]) == 0:
                    state["output_pending"] = True

        cycle += 1

    return {
        "divider_lanes": lanes,
        "finalizer_banks": banks,
        "divider_cycles_per_beat": divide_cycles,
        "per_bank_output_latency_cycles": output_latency_cycles,
        "per_bank_accept_interval_cycles": finalizer_accept_interval_cycles(lanes),
        "accept_events": accept_events,
        "result_events": result_events,
        "accepted_count": len(accept_events),
        "completed_count": len(result_events),
        "dispatch_stall_cycles": dispatch_stall_cycles,
        "order_fifo_high_watermark": high_watermark,
        "drain_cycles": cycle,
        "bank_accepted_count": [int(state["accepted_count"]) for state in bank_state],
        "bank_completed_count": [int(state["completed_count"]) for state in bank_state],
    }


def exact_banked_finalized_tree_service_manifest(
    *,
    clusters: int,
    heads: int = 32,
    divider_lanes: int = 8,
    finalizer_banks: int = 1,
) -> dict[str, int | bool | str]:
    banks = int(finalizer_banks)
    if banks < 1 or banks > 64:
        raise ValueError("finalizer_banks must be in [1, 64]")
    manifest = dict(exact_finalized_tree_service_manifest(clusters=clusters, heads=heads, divider_lanes=divider_lanes))
    manifest.update(
        {
            "finalizer_banks": banks,
            "order_fifo_depth": banks,
            "order_fifo_entry_bits": max(1, (banks - 1).bit_length()),
            "order_fifo_storage_bits": banks * max(1, (banks - 1).bit_length()),
            "ordering_contract": "round_robin_dispatch_fifo_retire",
            "per_bank_output_latency_cycles": finalizer_output_latency_cycles(divider_lanes),
            "per_bank_accept_interval_cycles": finalizer_accept_interval_cycles(divider_lanes),
            "minimum_banks_for_wrap_free_lane8_service": finalizer_accept_interval_cycles(8),
        }
    )
    return manifest


def exact_partial_producer_tree_service_manifest(
    *,
    producers: int = 2,
    clusters: int = 2,
    heads: int = 32,
    max_blocks: int = 16384,
    divider_lanes: int = 8,
    finalizer_banks: int = 59,
) -> dict[str, object]:
    producer_count = int(producers)
    cluster_count = int(clusters)
    head_count = int(heads)
    block_limit = int(max_blocks)
    if producer_count < 2 or producer_count > 16 or (producer_count & (producer_count - 1)):
        raise ValueError("producers must be a power of two in [2, 16]")
    if cluster_count < 2 or cluster_count > 16 or (cluster_count & (cluster_count - 1)):
        raise ValueError("clusters must be a power of two in [2, 16]")
    if producer_count != cluster_count:
        raise ValueError("producer-coupled exact-partial slice requires producers == clusters")
    if head_count < 1 or head_count > 32:
        raise ValueError("heads must be in [1, 32]")
    if block_limit < 8 or block_limit > 16384 or (block_limit & (block_limit - 1)):
        raise ValueError("max_blocks must be a power of two in [8, 16384]")
    manifest = dict(
        exact_banked_finalized_tree_service_manifest(
            clusters=cluster_count,
            heads=head_count,
            divider_lanes=divider_lanes,
            finalizer_banks=finalizer_banks,
        )
    )
    manifest.update(
        {
            "producers": producer_count,
            "clusters": cluster_count,
            "command_broadcast_mode": f"same_head_broadcast_to_all_{producer_count}_producers",
            "head_mapping_contract": "explicit_head_id_no_tile_or_wave_inference",
            "producer_input_contract": "per_producer_ready_valid_score_blocks_and_value_blocks",
            "producer_partial_protocol": {
                "command_id_bits": 16,
                "head_id_bits": HEAD_ID_BITS,
                "global_max_bits": SCORE_BITS,
                "exp_sum_bits": EXP_SUM_BITS,
                "slice_index_bits": SLICE_INDEX_BITS,
                "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
                "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
            },
            "finalized_protocol": {
                "command_id_bits": 16,
                "head_id_bits": HEAD_ID_BITS,
                "slice_index_bits": SLICE_INDEX_BITS,
                "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
                "final_link_bits_per_beat": FINAL_LINK_BITS,
            },
            "producer_block_workload_assumptions": {
                "command_block_count_range": [1, block_limit],
                "probe_block_count_per_head": 3,
                "probe_score_beats_per_block": 3,
                "multiple_heads_run_in_order": True,
                "no_tile_wave_to_head_aliasing": True,
            },
            "comparison_baseline_contract": "producer_parallel_then_reducer_staged",
            "comparison_cycle_origin": "producer_phase_starts_at_cycle0_reducer_phase_starts_after_parallel_producer_drain",
            "diagnostic_only_baseline": "producer_fully_serialized_then_reducer_staged",
            "llama_tile_cadence_unclosed": True,
            "remaining_abstractions": [
                "direct_328bit_exact_partial_links_unclosed",
                f"native_c{cluster_count}_overlap_only",
                "llama_16cluster_8tilewave_986cycle_mapping_open",
            ],
        }
    )
    return manifest


__all__ = [
    "EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS",
    "ExactFinalizedBeat",
    "ExactPartialBeat",
    "FINAL_PAYLOAD_BITS",
    "FINAL_LINK_BITS",
    "HEAD_ID_BITS",
    "LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS",
    "PARTIAL_PAYLOAD_BITS",
    "PARTIAL_LINK_BITS",
    "SLICE_LANES",
    "SLICE_INDEX_BITS",
    "VALUE_SLICES",
    "exact_partial_tree_service_manifest",
    "exact_finalized_tree_service_manifest",
    "exact_banked_finalized_tree_service_manifest",
    "exact_partial_producer_tree_service_manifest",
    "exact_banked_finalized_tree_full_wave_saturated_service",
    "finalizer_cycles_per_beat",
    "finalizer_output_latency_cycles",
    "finalizer_accept_interval_cycles",
    "finalize_partial_beat",
    "finalize_partial_beats",
    "finalize_partial_stream",
    "merge_balanced_partial_streams",
    "merge_partial_beats",
    "merge_partial_streams",
    "merge_partial_streams_via_local_normalization",
    "normalized_merge_guard_case",
    "pack_numerators",
    "partial_stream_from_blocks",
    "pack_final_values",
    "simulate_exact_finalizer",
    "simulate_exact_banked_finalizer",
    "unpack_final_values",
    "unpack_numerators",
]
