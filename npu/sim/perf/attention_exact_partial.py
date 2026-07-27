"""Exact streamed partial-state reference for score32 online reduction."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from npu.sim.perf.attention_online import (
    EXP_SUM_BITS,
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


__all__ = [
    "EXACT_STATE_BYTES_PER_CLUSTER_32_HEADS",
    "ExactPartialBeat",
    "HEAD_ID_BITS",
    "LEAF_STREAM_BYTES_PER_CLUSTER_32_HEADS",
    "PARTIAL_PAYLOAD_BITS",
    "PARTIAL_LINK_BITS",
    "SLICE_LANES",
    "SLICE_INDEX_BITS",
    "VALUE_SLICES",
    "exact_partial_tree_service_manifest",
    "finalize_partial_stream",
    "merge_balanced_partial_streams",
    "merge_partial_beats",
    "merge_partial_streams",
    "merge_partial_streams_via_local_normalization",
    "normalized_merge_guard_case",
    "pack_numerators",
    "partial_stream_from_blocks",
    "unpack_numerators",
]
