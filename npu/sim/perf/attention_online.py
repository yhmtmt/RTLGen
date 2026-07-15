"""Fixed-point online-softmax composition for scalable separated attention."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from npu.sim.perf.attention_separated import (
    AttentionSeparatedCommand,
    EXP_BUCKET_SHIFT,
    MAX_EXP_BUCKET,
    ROW_ELEMS,
    VALUE_DIM,
    WEIGHT_SCALE,
    _exp_lut,
    producer_result,
    result_ready,
)

MAX_CONTEXT_TOKENS = 131072
MAX_BLOCK_COUNT = MAX_CONTEXT_TOKENS // ROW_ELEMS
EXP_SUM_BITS = 33
WEIGHTED_NUMERATOR_BITS = 41
FINAL_VALUE_BITS = 40
MERGE_SCALE_BITS = 24
MERGE_SCALE = (1 << MERGE_SCALE_BITS) - 1
SCORE_BITS = 32


@dataclass(frozen=True)
class AttentionOnlineStats:
    max_score: int
    exp_sum: int
    weighted_numerator: tuple[int, ...]
    block_count: int

    def __post_init__(self) -> None:
        if len(self.weighted_numerator) != VALUE_DIM:
            raise ValueError(f"weighted_numerator must have {VALUE_DIM} lanes")
        if not 1 <= self.block_count <= MAX_BLOCK_COUNT:
            raise ValueError(f"block_count must be in [1, {MAX_BLOCK_COUNT}]")
        if not 0 <= self.exp_sum < (1 << EXP_SUM_BITS):
            raise ValueError(f"exp_sum does not fit {EXP_SUM_BITS} bits")
        limit = 1 << (WEIGHTED_NUMERATOR_BITS - 1)
        if any(not -limit <= value < limit for value in self.weighted_numerator):
            raise ValueError(f"weighted numerator does not fit {WEIGHTED_NUMERATOR_BITS} signed bits")


def _bucket(delta: int) -> int:
    return max(0, (int(delta) + (1 << (EXP_BUCKET_SHIFT - 1))) >> EXP_BUCKET_SHIFT)


def _online_exp_lut(bucket: int, *, output_scale: int = WEIGHT_SCALE) -> int:
    if bucket > MAX_EXP_BUCKET:
        return 0
    if output_scale == WEIGHT_SCALE:
        return _exp_lut(bucket)
    step = float(1 << EXP_BUCKET_SHIFT) / float(1 << 28)
    return max(1, int(math.exp(-(bucket * step)) * output_scale + 0.5))


def _round_div_signed(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    magnitude = (abs(numerator) + denominator // 2) // denominator
    return -magnitude if numerator < 0 else magnitude


def requantize_score(value: int, *, multiplier: int, shift: int) -> int:
    """Apply the decode-cluster score scale with symmetric rounding and S32 saturation."""
    if not -(1 << 31) <= int(value) < (1 << 31):
        raise ValueError("score input must fit signed 32 bits")
    if not 0 <= int(multiplier) < (1 << 32):
        raise ValueError("score multiplier must fit unsigned 32 bits")
    if not 0 <= int(shift) < (1 << 6):
        raise ValueError("score shift must fit unsigned 6 bits")
    product = int(value) * int(multiplier)
    if shift:
        magnitude = (abs(product) + (1 << (shift - 1))) >> shift
        scaled = -magnitude if product < 0 else magnitude
    else:
        scaled = product
    return min((1 << 31) - 1, max(-(1 << 31), scaled))


def requantize_score_row(
    values: Iterable[int],
    *,
    multiplier: int,
    shift: int,
) -> tuple[int, ...]:
    scores = tuple(int(value) for value in values)
    if len(scores) != ROW_ELEMS:
        raise ValueError(f"score row must contain {ROW_ELEMS} lanes")
    return tuple(requantize_score(value, multiplier=multiplier, shift=shift) for value in scores)


def _scale_unsigned(value: int, scale: int, *, scale_one: int) -> int:
    return (int(value) * int(scale) + scale_one // 2) // scale_one


def _scale_signed(value: int, scale: int, *, scale_one: int) -> int:
    return _round_div_signed(int(value) * int(scale), scale_one)


def block_stats(score_row: Iterable[int], value_matrix: Iterable[Iterable[int]]) -> AttentionOnlineStats:
    scores = [int(value) for value in score_row]
    values = [[int(value) for value in row] for row in value_matrix]
    if len(scores) != ROW_ELEMS or len(values) != ROW_ELEMS:
        raise ValueError(f"block must contain {ROW_ELEMS} score/value rows")
    if any(len(row) != VALUE_DIM for row in values):
        raise ValueError(f"each value row must contain {VALUE_DIM} lanes")

    maximum = max(scores)
    exponents = [_online_exp_lut(_bucket(maximum - score)) for score in scores]
    numerators = tuple(
        sum(exponents[row] * values[row][lane] for row in range(ROW_ELEMS))
        for lane in range(VALUE_DIM)
    )
    return AttentionOnlineStats(
        max_score=maximum,
        exp_sum=sum(exponents),
        weighted_numerator=numerators,
        block_count=1,
    )


def block_stats_with_global_max(
    score_row: Iterable[int],
    value_matrix: Iterable[Iterable[int]],
    *,
    global_max: int,
) -> AttentionOnlineStats:
    scores = [int(value) for value in score_row]
    values = [[int(value) for value in row] for row in value_matrix]
    if len(scores) != ROW_ELEMS or len(values) != ROW_ELEMS:
        raise ValueError(f"block must contain {ROW_ELEMS} score/value rows")
    if any(len(row) != VALUE_DIM for row in values):
        raise ValueError(f"each value row must contain {VALUE_DIM} lanes")
    if any(score > global_max for score in scores):
        raise ValueError("global_max must cover every score")
    exponents = [_online_exp_lut(_bucket(global_max - score)) for score in scores]
    return AttentionOnlineStats(
        max_score=global_max,
        exp_sum=sum(exponents),
        weighted_numerator=tuple(
            sum(exponents[row] * values[row][lane] for row in range(ROW_ELEMS))
            for lane in range(VALUE_DIM)
        ),
        block_count=1,
    )


def merge_stats(left: AttentionOnlineStats, right: AttentionOnlineStats) -> AttentionOnlineStats:
    block_count = left.block_count + right.block_count
    if block_count > MAX_BLOCK_COUNT:
        raise ValueError(f"merged block_count exceeds {MAX_BLOCK_COUNT}")
    maximum = max(left.max_score, right.max_score)
    left_scale = _online_exp_lut(_bucket(maximum - left.max_score), output_scale=MERGE_SCALE)
    right_scale = _online_exp_lut(_bucket(maximum - right.max_score), output_scale=MERGE_SCALE)
    exp_sum = _scale_unsigned(left.exp_sum, left_scale, scale_one=MERGE_SCALE) + _scale_unsigned(
        right.exp_sum, right_scale, scale_one=MERGE_SCALE
    )
    numerators = tuple(
        _scale_signed(left.weighted_numerator[lane], left_scale, scale_one=MERGE_SCALE)
        + _scale_signed(right.weighted_numerator[lane], right_scale, scale_one=MERGE_SCALE)
        for lane in range(VALUE_DIM)
    )
    return AttentionOnlineStats(
        max_score=maximum,
        exp_sum=exp_sum,
        weighted_numerator=numerators,
        block_count=block_count,
    )


def merge_sequence(blocks: Iterable[AttentionOnlineStats]) -> AttentionOnlineStats:
    iterator = iter(blocks)
    try:
        merged = next(iterator)
    except StopIteration as exc:
        raise ValueError("expected at least one block") from exc
    for block in iterator:
        merged = merge_stats(merged, block)
    return merged


def merge_balanced(blocks: Iterable[AttentionOnlineStats]) -> AttentionOnlineStats:
    level = list(blocks)
    if not level:
        raise ValueError("expected at least one block")
    while len(level) > 1:
        next_level: list[AttentionOnlineStats] = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                next_level.append(level[index])
            else:
                next_level.append(merge_stats(level[index], level[index + 1]))
        level = next_level
    return level[0]


def sum_same_max(blocks: Iterable[AttentionOnlineStats]) -> AttentionOnlineStats:
    values = list(blocks)
    if not values:
        raise ValueError("expected at least one block")
    maximum = values[0].max_score
    if any(block.max_score != maximum for block in values):
        raise ValueError("all blocks must use the same global max")
    return AttentionOnlineStats(
        max_score=maximum,
        exp_sum=sum(block.exp_sum for block in values),
        weighted_numerator=tuple(
            sum(block.weighted_numerator[lane] for block in values)
            for lane in range(VALUE_DIM)
        ),
        block_count=sum(block.block_count for block in values),
    )


def two_pass_stats(
    score_rows: Iterable[Iterable[int]],
    value_matrices: Iterable[Iterable[Iterable[int]]],
) -> AttentionOnlineStats:
    score_blocks = [[int(value) for value in row] for row in score_rows]
    value_blocks = [[[int(value) for value in lane_row] for lane_row in block] for block in value_matrices]
    if not score_blocks or len(score_blocks) != len(value_blocks):
        raise ValueError("score_rows and value_matrices must contain the same nonzero block count")
    maximum = max(max(row) for row in score_blocks)
    return sum_same_max(
        block_stats_with_global_max(scores, values, global_max=maximum)
        for scores, values in zip(score_blocks, value_blocks)
    )


def score_buffer_bytes(*, context_tokens: int, attention_heads: int, score_bits: int = 32) -> int:
    if context_tokens <= 0 or attention_heads <= 0 or score_bits <= 0 or score_bits % 8:
        raise ValueError("context_tokens, attention_heads, and byte-aligned score_bits must be positive")
    return context_tokens * attention_heads * (score_bits // 8)


def two_pass_command(command: AttentionSeparatedCommand, *, block_count: int) -> dict[str, object]:
    if block_count < 2 or block_count > MAX_BLOCK_COUNT:
        raise ValueError(f"block_count must be in [2, {MAX_BLOCK_COUNT}]")
    command = command.normalized()
    payloads = [
        producer_result(
            AttentionSeparatedCommand(
                command_id=(command.command_id + index) & 0xFFFF,
                seed=(command.seed ^ ((index * 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF,
            )
        )
        for index in range(block_count)
    ]
    stats = two_pass_stats(
        [payload["score_row"] for payload in payloads],
        [payload["value_matrix"] for payload in payloads],
    )
    return {
        "command_id": command.command_id,
        "seed": command.seed,
        "block_count": block_count,
        "global_max": stats.max_score,
        "exp_sum": stats.exp_sum,
        "value": list(finalize_value(stats)),
        "stats": stats,
    }


def simulate_two_pass(
    commands: Iterable[AttentionSeparatedCommand],
    *,
    block_count: int,
    scenario: str,
    max_cycles: int = 10000,
) -> dict[str, object]:
    command_list = [command.normalized() for command in commands]
    if scenario not in {"always_ready", "result_backpressure"}:
        raise ValueError(f"unsupported scenario: {scenario}")
    state = "idle"
    command_index = 0
    issue_index = stored_count = replay_index = 0
    producer_payload: dict[str, object] | None = None
    active: AttentionSeparatedCommand | None = None
    pending_result: dict[str, object] | None = None
    accept_events: list[dict[str, int]] = []
    result_events: list[dict[str, object]] = []

    for cycle in range(max_cycles):
        if len(result_events) == len(command_list):
            break
        old_state = state
        if old_state == "hold" and pending_result is not None and result_ready(scenario, cycle=cycle):
            result_events.append({"cycle": cycle, **pending_result})
            pending_result = None
            state = "idle"
        if old_state == "idle" and command_index < len(command_list):
            active = command_list[command_index]
            accept_events.append(
                {"cycle": cycle, "command_id": active.command_id, "seed": active.seed}
            )
            command_index += 1
            issue_index = stored_count = replay_index = 0
            state = "fill"
        elif old_state == "fill":
            if producer_payload is not None:
                producer_payload = None
                stored_count += 1
                if stored_count == block_count:
                    replay_index = 0
                    state = "replay"
            elif issue_index < block_count:
                assert active is not None
                producer_payload = producer_result(
                    AttentionSeparatedCommand(
                        command_id=(active.command_id + issue_index) & 0xFFFF,
                        seed=(active.seed ^ ((issue_index * 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF,
                    )
                )
                issue_index += 1
        elif old_state == "replay":
            replay_index += 1
            if replay_index == block_count:
                assert active is not None
                pending_result = two_pass_command(active, block_count=block_count)
                pending_result.pop("stats")
                state = "hold"
    else:
        raise RuntimeError(f"two-pass scenario {scenario} exceeded {max_cycles} cycles")
    return {
        "scenario": scenario,
        "block_count": block_count,
        "accepted_count": len(accept_events),
        "completed_count": len(result_events),
        "accept_events": accept_events,
        "result_events": result_events,
        "final_cycle": result_events[-1]["cycle"] if result_events else -1,
    }


def finalize_value(stats: AttentionOnlineStats) -> tuple[int, ...]:
    if stats.exp_sum <= 0:
        raise ValueError("cannot finalize an empty exponent sum")
    limit = 1 << (FINAL_VALUE_BITS - 1)
    values = tuple(
        _round_div_signed(numerator * WEIGHT_SCALE, stats.exp_sum)
        for numerator in stats.weighted_numerator
    )
    if any(not -limit <= value < limit for value in values):
        raise ValueError(f"final value does not fit {FINAL_VALUE_BITS} signed bits")
    return values


def width_bounds() -> dict[str, int]:
    max_exp_sum = MAX_CONTEXT_TOKENS * WEIGHT_SCALE
    max_weighted_numerator = MAX_CONTEXT_TOKENS * 128 * WEIGHT_SCALE
    return {
        "max_context_tokens": MAX_CONTEXT_TOKENS,
        "max_block_count": MAX_BLOCK_COUNT,
        "max_exp_sum": max_exp_sum,
        "exp_sum_bits_required": max_exp_sum.bit_length(),
        "exp_sum_bits": EXP_SUM_BITS,
        "max_weighted_numerator_magnitude": max_weighted_numerator,
        "weighted_numerator_signed_bits_required": max_weighted_numerator.bit_length() + 1,
        "weighted_numerator_bits": WEIGHTED_NUMERATOR_BITS,
        "merge_scale_bits": MERGE_SCALE_BITS,
    }


__all__ = [
    "AttentionOnlineStats",
    "EXP_SUM_BITS",
    "FINAL_VALUE_BITS",
    "MAX_BLOCK_COUNT",
    "MAX_CONTEXT_TOKENS",
    "MERGE_SCALE_BITS",
    "WEIGHTED_NUMERATOR_BITS",
    "block_stats",
    "block_stats_with_global_max",
    "finalize_value",
    "merge_sequence",
    "merge_balanced",
    "merge_stats",
    "requantize_score",
    "requantize_score_row",
    "score_buffer_bytes",
    "sum_same_max",
    "simulate_two_pass",
    "two_pass_command",
    "two_pass_stats",
    "width_bounds",
]
