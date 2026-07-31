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
LOCAL_TEMPORAL_WAVES = 8
LOCAL_CLUSTER_GQA8_HEAD_BASES = (0, 8, 16, 24)
SLICE_INDEX_BITS = (VALUE_SLICES - 1).bit_length()
PARTIAL_PAYLOAD_BITS = SLICE_LANES * WEIGHTED_NUMERATOR_BITS
PARTIAL_LINK_BITS = PARTIAL_PAYLOAD_BITS + 16 + HEAD_ID_BITS + SCORE_BITS + EXP_SUM_BITS + SLICE_INDEX_BITS + 1
EXACT_STATE_BITS_PER_HEAD = (VALUE_SLICES * PARTIAL_PAYLOAD_BITS) + SCORE_BITS + EXP_SUM_BITS
EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS = (EXACT_STATE_BITS_PER_HEAD * 32) // 8
LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS = (PARTIAL_LINK_BITS * VALUE_SLICES * 32) // 8
FINAL_PAYLOAD_BITS = SLICE_LANES * FINAL_VALUE_BITS
FINAL_LINK_BITS = FINAL_PAYLOAD_BITS + 16 + HEAD_ID_BITS + SLICE_INDEX_BITS + 1
FINALIZER_CONTROL_TRANSACTION_ID_BITS = 16
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


@dataclass(frozen=True)
class ExactLocalTemporalClusterComposition:
    wave_local_roots: tuple[tuple[ExactPartialBeat, ...], ...]
    temporal_aggregate: tuple[ExactPartialBeat, ...]


@dataclass(frozen=True)
class ExactLocalGlobalGqa8Composition:
    cluster_compositions: tuple[ExactLocalTemporalClusterComposition, ...]
    global_merged_partials: tuple[ExactPartialBeat, ...]
    finalized_beats: tuple[ExactFinalizedBeat, ...]


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


def _merge_equal_partial_streams(
    left: Iterable[ExactPartialBeat],
    right: Iterable[ExactPartialBeat],
) -> tuple[ExactPartialBeat, ...]:
    left_beats = tuple(left)
    right_beats = tuple(right)
    if not left_beats or len(left_beats) != len(right_beats):
        raise ValueError("partial streams must be non-empty and contain the same beat count")
    return tuple(merge_partial_beats(left_beats[index], right_beats[index]) for index in range(len(left_beats)))


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


def merge_staged_partial_streams(streams: Iterable[Iterable[ExactPartialBeat]]) -> tuple[ExactPartialBeat, ...]:
    level = [tuple(stream) for stream in streams]
    if not level:
        raise ValueError("expected at least one partial stream")
    expected_beats = len(level[0])
    if expected_beats == 0:
        raise ValueError("partial streams must be non-empty")
    if any(len(stream) != expected_beats for stream in level):
        raise ValueError("all partial streams must contain the same beat count")
    while len(level) > 1:
        next_level: list[tuple[ExactPartialBeat, ...]] = []
        index = 0
        while index < len(level):
            if index + 1 >= len(level):
                next_level.append(level[index])
            else:
                next_level.append(
                    tuple(
                        merge_partial_beats(level[index][beat_index], level[index + 1][beat_index])
                        for beat_index in range(expected_beats)
                    )
                )
            index += 2
        level = next_level
    return level[0]


def reduce_local_temporal_partial_waves(
    waves: Iterable[Iterable[Iterable[ExactPartialBeat]]],
    *,
    expected_waves: int = LOCAL_TEMPORAL_WAVES,
) -> tuple[ExactPartialBeat, ...]:
    wave_streams = [tuple(tuple(beat for beat in stream) for stream in wave) for wave in waves]
    if len(wave_streams) != int(expected_waves):
        raise ValueError(f"expected exactly {int(expected_waves)} waves")
    if not wave_streams[0]:
        raise ValueError("expected at least one producer stream per wave")
    aggregate: tuple[ExactPartialBeat, ...] | None = None
    for wave in wave_streams:
        if not wave:
            raise ValueError("expected at least one producer stream per wave")
        local_root = merge_staged_partial_streams(wave)
        aggregate = local_root if aggregate is None else _merge_equal_partial_streams(aggregate, local_root)
    if aggregate is None:
        raise AssertionError("unreachable")
    return aggregate


def compose_local_temporal_cluster_exact(
    waves: Iterable[Iterable[Iterable[ExactPartialBeat]]],
    *,
    expected_waves: int = LOCAL_TEMPORAL_WAVES,
) -> ExactLocalTemporalClusterComposition:
    wave_streams = [tuple(tuple(beat for beat in stream) for stream in wave) for wave in waves]
    if len(wave_streams) != int(expected_waves):
        raise ValueError(f"expected exactly {int(expected_waves)} waves")
    if not wave_streams[0]:
        raise ValueError("expected at least one producer stream per wave")
    wave_local_roots: list[tuple[ExactPartialBeat, ...]] = []
    temporal_aggregate: tuple[ExactPartialBeat, ...] | None = None
    for wave in wave_streams:
        if not wave:
            raise ValueError("expected at least one producer stream per wave")
        local_root = merge_staged_partial_streams(wave)
        wave_local_roots.append(local_root)
        temporal_aggregate = (
            local_root
            if temporal_aggregate is None
            else _merge_equal_partial_streams(temporal_aggregate, local_root)
        )
    if temporal_aggregate is None:
        raise AssertionError("unreachable")
    return ExactLocalTemporalClusterComposition(
        wave_local_roots=tuple(wave_local_roots),
        temporal_aggregate=temporal_aggregate,
    )


def compose_local16_global_tree_gqa8_exact(
    clusters: Iterable[Iterable[Iterable[Iterable[ExactPartialBeat]]]],
    *,
    expected_clusters: int = 16,
    expected_waves: int = LOCAL_TEMPORAL_WAVES,
) -> ExactLocalGlobalGqa8Composition:
    cluster_compositions = tuple(
        compose_local_temporal_cluster_exact(cluster, expected_waves=expected_waves) for cluster in clusters
    )
    if len(cluster_compositions) != int(expected_clusters):
        raise ValueError(f"expected exactly {int(expected_clusters)} clusters")
    global_merged_partials = merge_balanced_partial_streams(
        composition.temporal_aggregate for composition in cluster_compositions
    )
    finalized_beats = finalize_partial_beats(global_merged_partials)
    return ExactLocalGlobalGqa8Composition(
        cluster_compositions=cluster_compositions,
        global_merged_partials=global_merged_partials,
        finalized_beats=finalized_beats,
    )


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


def exact_partial_staged_tree_service_manifest(*, producers: int, heads: int = 32) -> dict[str, int | bool | str]:
    producer_count = int(producers)
    head_count = int(heads)
    if producer_count < 2 or producer_count > 64:
        raise ValueError("producers must be in [2, 64]")
    if head_count < 1:
        raise ValueError("heads must be positive")
    stages = int(math.ceil(math.log2(producer_count)))
    exact_state_bytes_per_producer = (EXACT_STATE_BITS_PER_HEAD * head_count) // 8
    leaf_stream_bytes_per_producer = (PARTIAL_LINK_BITS * VALUE_SLICES * head_count) // 8
    return {
        "producers": producer_count,
        "heads": head_count,
        "tree_stages": stages,
        "tree_nodes": producer_count - 1,
        "value_slices": VALUE_SLICES,
        "slice_lanes": SLICE_LANES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "exact_state_bytes_per_producer": exact_state_bytes_per_producer,
        "leaf_stream_bytes_per_producer": leaf_stream_bytes_per_producer,
        "total_leaf_stream_bytes": leaf_stream_bytes_per_producer * producer_count,
        "staging_contract": "pairwise_ready_valid_exact_merge_with_odd_leaf_carry",
        "direct_328bit_links_unclosed": True,
        "final_divider_embodied": False,
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


def exact_finalizer_bank_control_service_manifest(
    *,
    heads: int = 32,
    divider_lanes: int = 8,
    finalizer_banks: int = 1,
) -> dict[str, int | bool | str]:
    banks = int(finalizer_banks)
    head_count = int(heads)
    lanes = int(divider_lanes)
    if head_count < 1 or head_count > 32:
        raise ValueError("heads must be in [1, 32]")
    if lanes not in {1, 2, 4, 8}:
        raise ValueError("divider_lanes must be one of 1, 2, 4, 8")
    if banks < 1 or banks > 64:
        raise ValueError("finalizer_banks must be in [1, 64]")
    return {
        "heads": head_count,
        "value_slices": VALUE_SLICES,
        "finalizer_banks": banks,
        "divider_lanes": lanes,
        "synthetic_transaction_id_bits": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "tree_issue_link_bits_per_beat": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "bank_issue_link_bits_per_beat": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "bank_return_link_bits_per_beat": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "root_retire_link_bits_per_beat": FINALIZER_CONTROL_TRANSACTION_ID_BITS,
        "order_fifo_depth": banks,
        "order_fifo_entry_bits": max(1, (banks - 1).bit_length()),
        "order_fifo_storage_bits": banks * max(1, (banks - 1).bit_length()),
        "ordering_contract": "round_robin_dispatch_fifo_retire",
        "per_bank_output_latency_cycles": finalizer_output_latency_cycles(lanes),
        "per_bank_accept_interval_cycles": finalizer_accept_interval_cycles(lanes),
        "minimum_banks_for_wrap_free_lane8_service": finalizer_accept_interval_cycles(8),
        "full_llama_wave_root_beats": head_count * VALUE_SLICES,
        "control_only_embodied": True,
        "bank_arithmetic_embodied": False,
        "tree_payload_fanout_embodied": False,
        "root_payload_mux_embodied": False,
        "exact_service_model_cycle_equivalence": True,
    }


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


def exact_partial_dual_stream_gqa8_producer_service_manifest(
    *,
    heads: int = 32,
    max_blocks: int = 8,
    command_count: int | None = None,
    blocks_per_stream: int = 2,
    block_counts_per_stream: tuple[int, ...] | None = None,
    head_dim: int = 3,
    head_bases: tuple[int, ...] | None = None,
    llama_wave_reference_cycles: int | None = None,
) -> dict[str, object]:
    head_count = int(heads)
    block_limit = int(max_blocks)
    resolved_command_count = int(command_count if command_count is not None else head_count // 8)
    resolved_blocks_per_stream = int(blocks_per_stream)
    resolved_head_dim = int(head_dim)
    if head_count < 8 or head_count > 32 or head_count % 8:
        raise ValueError("heads must be a multiple of 8 in [8, 32]")
    if block_limit < 8 or block_limit > 16384 or (block_limit & (block_limit - 1)):
        raise ValueError("max_blocks must be a power of two in [8, 16384]")
    if resolved_command_count < 1:
        raise ValueError("command_count must be positive")
    if resolved_head_dim < 1:
        raise ValueError("head_dim must be positive")
    if block_counts_per_stream is None:
        if resolved_blocks_per_stream < 1 or resolved_blocks_per_stream > block_limit:
            raise ValueError("blocks_per_stream must be in [1, max_blocks]")
        block_counts = tuple(resolved_blocks_per_stream for _ in range(resolved_command_count))
    else:
        block_counts = tuple(int(value) for value in block_counts_per_stream)
        if len(block_counts) != resolved_command_count:
            raise ValueError("block_counts_per_stream length must match command_count")
        if any(value < 1 or value > block_limit for value in block_counts):
            raise ValueError("block_counts_per_stream entries must be in [1, max_blocks]")
        resolved_blocks_per_stream = max(block_counts)
    if head_bases is None:
        bases = tuple((group % (head_count // 8)) * 8 for group in range(resolved_command_count))
    else:
        bases = tuple(int(value) for value in head_bases)
    if len(bases) != resolved_command_count:
        raise ValueError("head_bases length must match command_count")
    if any(base < 0 or base > 24 or base % 8 for base in bases):
        raise ValueError("head_bases entries must be aligned to 8 in [0, 24]")
    cadence_reference = {
        "reference_cycles": int(llama_wave_reference_cycles),
        "interpretation": "functional_service_evidence_only_no_frontier_revision",
    } if llama_wave_reference_cycles is not None else None
    return {
        "streams": 2,
        "query_heads_per_stream": 8,
        "query_head_groups": head_count // 8,
        "token_lanes_per_head": 8,
        "structural_score_macs_per_cycle": 2 * 8 * 8,
        "command_broadcast_mode": "same_head_base_broadcast_to_both_stream_groups",
        "head_mapping_contract": "explicit_head_base_plus_lane_no_tile_or_wave_inference",
        "producer_input_contract": "packed_dual_stream_query_key_atomic_ready_valid",
        "value_memory_contract": "per_stream_gqa_coalesced_value_reads",
        "output_schedule_contract": "serialized_head_then_slice_exact_partial_stream",
        "producer_partial_protocol": {
            "command_id_bits": 16,
            "head_id_bits": HEAD_ID_BITS,
            "global_max_bits": SCORE_BITS,
            "exp_sum_bits": EXP_SUM_BITS,
            "slice_index_bits": SLICE_INDEX_BITS,
            "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
            "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        },
        "producer_block_workload_assumptions": {
            "command_block_count_range": [1, block_limit],
            "probe_command_count": resolved_command_count,
            "per_wave_local_block_ceiling_per_stream": 2,
            "persistent_local_reducer_waves": 8,
            "probe_blocks_per_stream": resolved_blocks_per_stream,
            "probe_block_counts_per_stream": list(block_counts),
            "probe_blocks_per_stream_uniform": len(set(block_counts)) == 1,
            "probe_head_dim": resolved_head_dim,
            "probe_head_bases": list(bases),
            "probe_total_heads": head_count,
            "probe_token_streams": 2,
            "multiple_head_groups_run_in_order": True,
            "head_base_alignment_bits": 3,
            "global_tile_tokens": 1024,
            "global_tile_token_blocks": 128,
            "per_datapath_group_commands_per_wave": 4,
            "worst_loaded_total_blocks_per_stream_per_datapath_per_wave": 5,
            "worst_loaded_two_block_commands_per_datapath_per_wave": 1,
        },
        "comparison_baseline_contract": "python_structured_exact_partial_stream_reference",
        "comparison_cycle_origin": "cycle0_on_atomic_dual_stream_input_issue",
        "diagnostic_only_baseline": "none",
        "llama_wave_functional_service_reference": cadence_reference,
        "remaining_abstractions": [
            "53or54_way_global_cluster_aggregation_open",
            "8_wave_persistent_state_open",
            "noc_sram_ppa_open",
        ],
    }


def exact_local_temporal_reducer_service_manifest(
    *,
    producers: int,
    waves: int = LOCAL_TEMPORAL_WAVES,
    heads: int = 1,
) -> dict[str, object]:
    producer_count = int(producers)
    wave_count = int(waves)
    head_count = int(heads)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    if wave_count != LOCAL_TEMPORAL_WAVES:
        raise ValueError(f"waves must be exactly {LOCAL_TEMPORAL_WAVES}")
    if head_count < 1 or head_count > 32:
        raise ValueError("heads must be in [1, 32]")
    local_tree = exact_partial_staged_tree_service_manifest(producers=producer_count, heads=head_count)
    return {
        "producers": producer_count,
        "persistent_waves": wave_count,
        "heads": head_count,
        "tree_stages": local_tree["tree_stages"],
        "tree_nodes": local_tree["tree_nodes"],
        "value_slices": VALUE_SLICES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "command_head_contract": "explicit_command_id_head_id_slice_last_metadata_per_beat",
        "local_reduction_contract": "staged_exact_merge_with_odd_leaf_carry_until_single_local_root",
        "temporal_accumulation_contract": "merge_local_root_into_persistent_exact_state_for_exactly_8_waves_then_emit",
        "comparison_baseline_contract": "python_structured_local_temporal_exact_partial_reference",
        "comparison_cycle_origin": "cycle0_on_first_leaf_issue_of_wave0",
        "diagnostic_only_baseline": "none",
        "producer_partial_protocol": {
            "command_id_bits": 16,
            "head_id_bits": HEAD_ID_BITS,
            "global_max_bits": SCORE_BITS,
            "exp_sum_bits": EXP_SUM_BITS,
            "slice_index_bits": SLICE_INDEX_BITS,
            "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
            "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        },
        "remaining_abstractions": [
            "producer_fan_in_wiring_open",
            "noc_sram_ppa_open",
            "global_c16_exact_reduction_open",
        ],
    }


def exact_local_temporal_reducer_gqa8_service_manifest(
    *,
    producers: int,
    waves: int = LOCAL_TEMPORAL_WAVES,
    head_groups: int = 2,
) -> dict[str, object]:
    producer_count = int(producers)
    wave_count = int(waves)
    group_count = int(head_groups)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    if wave_count != LOCAL_TEMPORAL_WAVES:
        raise ValueError(f"waves must be exactly {LOCAL_TEMPORAL_WAVES}")
    if group_count < 1 or group_count > 4:
        raise ValueError("head_groups must be in [1, 4]")
    local_tree = exact_partial_staged_tree_service_manifest(producers=producer_count, heads=8 * group_count)
    return {
        "producers": producer_count,
        "persistent_waves": wave_count,
        "query_head_groups": group_count,
        "query_heads_per_group": 8,
        "value_slices": VALUE_SLICES,
        "beats_per_wave": 8 * VALUE_SLICES,
        "beats_per_output_group": 8 * VALUE_SLICES,
        "tree_stages": local_tree["tree_stages"],
        "tree_nodes": local_tree["tree_nodes"],
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "command_head_contract": "explicit_head_base_plus_lane_serialized_head_major_slice_minor_stream",
        "wave_terminal_contract": "advance_only_on_validated_head_lane7_slice15_after_128_beats",
        "local_reduction_contract": "staged_exact_merge_with_odd_leaf_carry_until_single_local_root",
        "temporal_accumulation_contract": "merge_local_root_into_128_banked_persistent_exact_state_for_exactly_8_waves_then_emit_128_beats",
        "comparison_baseline_contract": "python_structured_gqa8_local_temporal_exact_partial_reference",
        "comparison_cycle_origin": "cycle0_on_first_leaf_issue_of_group0_wave0",
        "diagnostic_only_baseline": "none",
        "producer_partial_protocol": {
            "command_id_bits": 16,
            "head_id_bits": HEAD_ID_BITS,
            "global_max_bits": SCORE_BITS,
            "exp_sum_bits": EXP_SUM_BITS,
            "slice_index_bits": SLICE_INDEX_BITS,
            "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
            "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        },
        "remaining_abstractions": [
            "producer_to_local_reducer_structural_fan_in_open",
            "noc_sram_ppa_open",
            "global_c16_exact_reduction_open",
        ],
    }


def exact_local_cluster_gqa8_extra_producers(*, producers: int, group_index: int) -> tuple[int, ...]:
    producer_count = int(producers)
    resolved_group_index = int(group_index)
    if producer_count == 53:
        group_windows = ((0, 11), (11, 22), (22, 33), (33, 44))
    elif producer_count == 54:
        group_windows = ((0, 10), (10, 20), (20, 30), (30, 40))
    else:
        raise ValueError("producers must be exactly 53 or 54")
    if resolved_group_index < 0 or resolved_group_index >= len(group_windows):
        raise ValueError("group_index must be in [0, 3]")
    start, stop = group_windows[resolved_group_index]
    return tuple(range(start, stop))


def exact_local_cluster_gqa8_command_block_counts(*, producers: int, group_index: int) -> tuple[int, ...]:
    producer_count = int(producers)
    extras = set(exact_local_cluster_gqa8_extra_producers(producers=producer_count, group_index=group_index))
    return tuple(2 if producer_index in extras else 1 for producer_index in range(producer_count))


def exact_local_cluster_gqa8_service_manifest(
    *,
    producers: int,
    waves: int = LOCAL_TEMPORAL_WAVES,
    head_bases: Iterable[int] = LOCAL_CLUSTER_GQA8_HEAD_BASES,
) -> dict[str, object]:
    producer_count = int(producers)
    wave_count = int(waves)
    resolved_head_bases = tuple(int(value) for value in head_bases)
    if producer_count not in {53, 54}:
        raise ValueError("producers must be exactly 53 or 54")
    if wave_count != LOCAL_TEMPORAL_WAVES:
        raise ValueError(f"waves must be exactly {LOCAL_TEMPORAL_WAVES}")
    if resolved_head_bases != LOCAL_CLUSTER_GQA8_HEAD_BASES:
        raise ValueError(f"head_bases must be exactly {LOCAL_CLUSTER_GQA8_HEAD_BASES}")

    reducer_manifest = exact_local_temporal_reducer_gqa8_service_manifest(
        producers=producer_count,
        waves=wave_count,
        head_groups=len(resolved_head_bases),
    )
    per_group_extra_producers = [
        list(exact_local_cluster_gqa8_extra_producers(producers=producer_count, group_index=group_index))
        for group_index in range(len(resolved_head_bases))
    ]
    per_group_block_counts = [
        list(exact_local_cluster_gqa8_command_block_counts(producers=producer_count, group_index=group_index))
        for group_index in range(len(resolved_head_bases))
    ]
    per_group_total_blocks_per_stream = [sum(group_counts) for group_counts in per_group_block_counts]
    if any(total != 64 for total in per_group_total_blocks_per_stream):
        raise AssertionError("every corrected GQA8 local-cluster group must cover exactly 64 blocks per stream")

    return {
        "producers": producer_count,
        "persistent_waves": wave_count,
        "query_head_groups": len(resolved_head_bases),
        "query_heads_per_group": 8,
        "head_bases": list(resolved_head_bases),
        "group_major_wave_commands_per_group": wave_count,
        "full_run_wave_command_count": len(resolved_head_bases) * wave_count,
        "max_blocks": 8,
        "per_producer_command_block_count_bits": 15,
        "per_group_extra_producers": per_group_extra_producers,
        "per_group_command_block_counts": per_group_block_counts,
        "per_group_total_blocks_per_stream": per_group_total_blocks_per_stream,
        "value_slices": VALUE_SLICES,
        "aggregate_output_beats_per_group": 8 * VALUE_SLICES,
        "aggregate_output_beats_per_full_run": len(resolved_head_bases) * 8 * VALUE_SLICES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "top_command_contract": "broadcast_command_id_head_base_multiplier_shift_with_packed_per_producer_block_counts",
        "atomic_command_issue_contract": "all_producers_accept_same_wave_command_same_cycle_or_none",
        "producer_input_contract": "independent_per_producer_dual_stream_query_key_last_ready_valid",
        "value_memory_contract": "independent_per_producer_dual_stream_value_request_response_lanes",
        "producer_leaf_wiring_contract": "index_preserving_direct_producer_result_leaf_connection_into_local_temporal_reducer",
        "local_reduction_contract": reducer_manifest["local_reduction_contract"],
        "temporal_accumulation_contract": "group_major_same_logical_command_across_8_waves_then_emit_before_next_head_base",
        "comparison_baseline_contract": (
            "python_structured_producer_reference_then_staged_p53p54_merge_then_group_major_8_wave_temporal_merge"
        ),
        "comparison_cycle_origin": "cycle0_on_first_atomic_wave_command_issue_for_head_base0_wave0",
        "diagnostic_only_baseline": "none",
        "remaining_abstractions": [
            "noc_sram_ppa_open",
            "global_c16_exact_reduction_open",
        ],
        "reducer_service_model": reducer_manifest,
    }


def exact_local16_global_tree_gqa8_service_manifest(
    *,
    cluster_producers: Iterable[int],
    waves: int = LOCAL_TEMPORAL_WAVES,
    head_groups: int = 2,
    divider_lanes: int = 8,
    finalizer_banks: int = 59,
) -> dict[str, object]:
    producer_counts = tuple(int(count) for count in cluster_producers)
    if len(producer_counts) != 16:
        raise ValueError("cluster_producers must contain exactly 16 entries")
    if producer_counts != tuple([54] * 8 + [53] * 8):
        raise ValueError("cluster_producers must be exactly eight 54s followed by eight 53s")
    if int(waves) != LOCAL_TEMPORAL_WAVES:
        raise ValueError(f"waves must be exactly {LOCAL_TEMPORAL_WAVES}")
    if int(head_groups) < 1 or int(head_groups) > 4:
        raise ValueError("head_groups must be in [1, 4]")
    if int(divider_lanes) != 8:
        raise ValueError("divider_lanes must remain fixed at 8")
    if int(finalizer_banks) != 59:
        raise ValueError("finalizer_banks must remain fixed at 59")

    global_service = exact_banked_finalized_tree_service_manifest(
        clusters=16,
        heads=8 * int(head_groups),
        divider_lanes=int(divider_lanes),
        finalizer_banks=int(finalizer_banks),
    )
    return {
        "clusters": 16,
        "cluster_producers": list(producer_counts),
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": sum(producer_counts),
        "total_value_memory_lanes": 2 * sum(producer_counts),
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "query_head_groups": int(head_groups),
        "query_heads_per_group": 8,
        "value_slices": VALUE_SLICES,
        "local_aggregate_beats_per_group": 8 * VALUE_SLICES,
        "global_finalized_beats_per_group": 8 * VALUE_SLICES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "command_head_contract": "one_shared_atomic_wave_command_id_head_base_multiplier_shift_across_all_16_clusters",
        "command_block_count_contract": (
            "derived_internally_from_head_base_with_p54_ranges_0_9_10_19_20_29_30_39_"
            "and_p53_ranges_0_10_11_21_22_32_33_43"
        ),
        "producer_input_contract": "independent_flattened_query_key_ready_valid_inputs_for_all_856_producers",
        "value_memory_contract": "independent_flattened_request_response_interfaces_for_all_1712_stream_lanes",
        "local_reduction_contract": "per_cluster_staged_exact_merge_with_odd_leaf_carry_until_single_local_root_per_beat",
        "temporal_accumulation_contract": "per_cluster_merge_local_root_into_128_banked_persistent_exact_state_for_exactly_8_waves",
        "global_reduction_contract": "sixteen_cluster_radix2_exact_merge_then_ordered_banked_finalization",
        "comparison_baseline_contract": "python_structured_full_row_producer_local16_global_exact_gqa8_reference",
        "comparison_cycle_origin": "cycle0_on_first_atomic_wave_command_issue_across_all_16_clusters",
        "diagnostic_only_baseline": "none",
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
        "global_tree_contract": {
            "clusters": 16,
            "radix": 2,
            "divider_lanes": int(divider_lanes),
            "finalizer_banks": int(finalizer_banks),
            "compatible_with_full_heads": 32,
            "measured_probe_heads": 8 * int(head_groups),
            "per_bank_output_latency_cycles": global_service["per_bank_output_latency_cycles"],
            "per_bank_accept_interval_cycles": global_service["per_bank_accept_interval_cycles"],
        },
        "remaining_abstractions": [
            "external_query_key_source_open",
            "external_value_memory_system_open",
            "physical_ppa_open",
        ],
    }


def exact_local16_global_tree_cluster_sram_gqa8_service_manifest(
    *,
    cluster_producers: Iterable[int],
    divider_lanes: int = 8,
    finalizer_banks: int = 59,
) -> dict[str, object]:
    producer_counts = tuple(int(count) for count in cluster_producers)
    if len(producer_counts) != 16:
        raise ValueError("cluster_producers must contain exactly 16 entries")
    if producer_counts != tuple([54] * 8 + [53] * 8):
        raise ValueError("cluster_producers must be exactly eight 54s followed by eight 53s")
    if int(divider_lanes) != 8:
        raise ValueError("divider_lanes must remain fixed at 8")
    if int(finalizer_banks) != 59:
        raise ValueError("finalizer_banks must remain fixed at 59")

    from npu.sim.perf.attention_score32_exact_cluster_sram_service_gqa8 import cluster_sram_service_manifest

    global_service = exact_banked_finalized_tree_service_manifest(
        clusters=16,
        heads=32,
        divider_lanes=int(divider_lanes),
        finalizer_banks=int(finalizer_banks),
    )
    per_cluster_lanes = [2 * producer_count for producer_count in producer_counts]
    return {
        "clusters": 16,
        "cluster_producers": list(producer_counts),
        "clusters_with_54_producers": 8,
        "clusters_with_53_producers": 8,
        "total_local_producers": sum(producer_counts),
        "internal_value_memory_lanes": sum(per_cluster_lanes),
        "per_cluster_internal_value_memory_lanes": per_cluster_lanes,
        "external_fill_interfaces": 16,
        "persistent_waves": LOCAL_TEMPORAL_WAVES,
        "query_head_groups": 4,
        "query_heads_per_group": 8,
        "value_slices": VALUE_SLICES,
        "partial_payload_bits_per_beat": PARTIAL_PAYLOAD_BITS,
        "partial_link_bits_per_beat": PARTIAL_LINK_BITS,
        "final_payload_bits_per_beat": FINAL_PAYLOAD_BITS,
        "final_link_bits_per_beat": FINAL_LINK_BITS,
        "command_head_contract": "one_shared_atomic_wave_command_id_head_base_multiplier_shift_across_all_16_clusters",
        "command_wave_contract": "implicit_group_major_schedule_head_bases_0_8_16_24_each_wave_0_to_7_reset_to_head0_wave0",
        "command_block_count_contract": (
            "derived_internally_from_head_base_with_p54_ranges_0_9_10_19_20_29_30_39_"
            "and_p53_ranges_0_10_11_21_22_32_33_43"
        ),
        "producer_input_contract": "independent_flattened_query_key_ready_valid_inputs_for_all_856_producers",
        "external_fill_contract": (
            "sixteen_per_cluster_hbm_return_fill_target_and_fill_row_channels_with_exact_command_id_head_base_wave_"
            "and_buffer_sel_equal_to_wave_index_lsb"
        ),
        "fill_prefetch_window_contract": (
            "reject_invalid_metadata_and_accept_only_current_expected_command_or_immediate_group_major_successor"
        ),
        "internal_value_memory_contract": (
            "exactly_one_local_p54_or_p53_sram_endpoint_per_cluster_with_index_preserving_dual_stream_lane_wiring"
        ),
        "local_reduction_contract": "per_cluster_staged_exact_merge_with_odd_leaf_carry_until_single_local_root_per_beat",
        "temporal_accumulation_contract": "per_cluster_merge_local_root_into_128_banked_persistent_exact_state_for_exactly_8_waves",
        "release_invariant_contract": (
            "release_once_per_wave_after_every_real_producer_command_completed_count_advances_and_"
            "endpoint_outstanding_response_occupancy_is_zero"
        ),
        "buffer_mapping_contract": "double_buffer_select_is_deterministic_and_equals_wave_index_lsb",
        "global_reduction_contract": "sixteen_cluster_radix2_exact_merge_then_ordered_banked_finalization",
        "comparison_baseline_contract": "python_structured_full_row_producer_local16_global_exact_gqa8_reference",
        "comparison_cycle_origin": "cycle0_on_first_atomic_wave_command_issue_for_head_base0_wave0",
        "diagnostic_only_baseline": "none",
        "global_tree_contract": {
            "clusters": 16,
            "radix": 2,
            "divider_lanes": int(divider_lanes),
            "finalizer_banks": int(finalizer_banks),
            "compatible_with_full_heads": 32,
            "measured_probe_heads": 32,
            "per_bank_output_latency_cycles": global_service["per_bank_output_latency_cycles"],
            "per_bank_accept_interval_cycles": global_service["per_bank_accept_interval_cycles"],
        },
        "per_cluster_sram_endpoint_service_models": {
            "p54": cluster_sram_service_manifest(producers=54),
            "p53": cluster_sram_service_manifest(producers=53),
        },
        "remaining_abstractions": [
            "external_hbm_return_fill_plane_open",
            "external_mesh_noc_fill_transport_open",
            "physical_ppa_open",
        ],
    }


__all__ = [
    "EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS",
    "ExactFinalizedBeat",
    "ExactLocalGlobalGqa8Composition",
    "ExactLocalTemporalClusterComposition",
    "ExactPartialBeat",
    "FINALIZER_CONTROL_TRANSACTION_ID_BITS",
    "FINAL_PAYLOAD_BITS",
    "FINAL_LINK_BITS",
    "HEAD_ID_BITS",
    "LOCAL_TEMPORAL_WAVES",
    "LOCAL_CLUSTER_GQA8_HEAD_BASES",
    "LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS",
    "PARTIAL_PAYLOAD_BITS",
    "PARTIAL_LINK_BITS",
    "SLICE_LANES",
    "SLICE_INDEX_BITS",
    "VALUE_SLICES",
    "exact_local16_global_tree_cluster_sram_gqa8_service_manifest",
    "exact_partial_tree_service_manifest",
    "exact_partial_staged_tree_service_manifest",
    "compose_local16_global_tree_gqa8_exact",
    "compose_local_temporal_cluster_exact",
    "exact_local16_global_tree_gqa8_service_manifest",
    "exact_finalized_tree_service_manifest",
    "exact_banked_finalized_tree_service_manifest",
    "exact_finalizer_bank_control_service_manifest",
    "exact_local_temporal_reducer_service_manifest",
    "exact_local_temporal_reducer_gqa8_service_manifest",
    "exact_local_cluster_gqa8_extra_producers",
    "exact_local_cluster_gqa8_command_block_counts",
    "exact_local_cluster_gqa8_service_manifest",
    "exact_partial_producer_tree_service_manifest",
    "exact_partial_dual_stream_gqa8_producer_service_manifest",
    "exact_banked_finalized_tree_full_wave_saturated_service",
    "finalizer_cycles_per_beat",
    "finalizer_output_latency_cycles",
    "finalizer_accept_interval_cycles",
    "finalize_partial_beat",
    "finalize_partial_beats",
    "finalize_partial_stream",
    "merge_balanced_partial_streams",
    "merge_staged_partial_streams",
    "merge_partial_beats",
    "merge_partial_streams",
    "merge_partial_streams_via_local_normalization",
    "normalized_merge_guard_case",
    "pack_numerators",
    "partial_stream_from_blocks",
    "pack_final_values",
    "simulate_exact_finalizer",
    "simulate_exact_banked_finalizer",
    "reduce_local_temporal_partial_waves",
    "unpack_final_values",
    "unpack_numerators",
]
