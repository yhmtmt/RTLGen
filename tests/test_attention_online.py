from dataclasses import replace

import pytest

from npu.sim.perf.attention_online import (
    AttentionOnlineStats,
    block_stats,
    finalize_value,
    merge_sequence,
    merge_stats,
    requantize_score,
    requantize_score_row,
    score_buffer_bytes,
    simulate_two_pass,
    two_pass_command,
    two_pass_stats,
    width_bounds,
)
from npu.sim.perf.attention_separated import command_tensors, default_commands, producer_result


def _stats(index: int) -> AttentionOnlineStats:
    command = default_commands(index + 1)[index]
    payload = producer_result(command)
    return block_stats(payload["score_row"], payload["value_matrix"])


def test_attention_online_widths_cover_llama7b_context() -> None:
    bounds = width_bounds()

    assert bounds["max_context_tokens"] == 131072
    assert bounds["max_block_count"] == 16384
    assert bounds["exp_sum_bits_required"] <= bounds["exp_sum_bits"]
    assert bounds["weighted_numerator_signed_bits_required"] <= bounds["weighted_numerator_bits"]


def test_attention_score_requantization_rounds_symmetrically() -> None:
    assert requantize_score(3, multiplier=1, shift=1) == 2
    assert requantize_score(-3, multiplier=1, shift=1) == -2
    assert requantize_score(1, multiplier=1, shift=1) == 1
    assert requantize_score(-1, multiplier=1, shift=1) == -1
    assert requantize_score(-7, multiplier=3, shift=0) == -21


def test_attention_score_requantization_saturates_signed_32_bits() -> None:
    assert requantize_score((1 << 31) - 1, multiplier=(1 << 32) - 1, shift=0) == (1 << 31) - 1
    assert requantize_score(-(1 << 31), multiplier=(1 << 32) - 1, shift=0) == -(1 << 31)
    assert requantize_score_row(range(8), multiplier=7, shift=2) == (0, 2, 4, 5, 7, 9, 11, 12)


@pytest.mark.parametrize(
    ("value", "multiplier", "shift", "message"),
    [
        (1 << 31, 1, 0, "signed 32"),
        (0, 1 << 32, 0, "unsigned 32"),
        (0, 1, 64, "unsigned 6"),
    ],
)
def test_attention_score_requantization_rejects_out_of_range_contract(
    value: int,
    multiplier: int,
    shift: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        requantize_score(value, multiplier=multiplier, shift=shift)


def test_attention_online_identity_scale_preserves_left_stats() -> None:
    left = _stats(0)
    zero_right = replace(
        _stats(1),
        max_score=left.max_score,
        exp_sum=1,
        weighted_numerator=(0,) * 8,
    )

    merged = merge_stats(left, zero_right)

    assert merged.max_score == left.max_score
    assert merged.exp_sum == left.exp_sum + 1
    assert merged.weighted_numerator == left.weighted_numerator


def test_attention_online_zeroes_blocks_beyond_lut_range() -> None:
    left = _stats(0)
    low = replace(_stats(1), max_score=left.max_score - (9 << 28))

    merged = merge_stats(left, low)

    assert merged.exp_sum == left.exp_sum
    assert merged.weighted_numerator == left.weighted_numerator


def test_attention_online_merge_is_deterministic_and_finalizable() -> None:
    blocks = [_stats(index) for index in range(8)]

    first = merge_sequence(blocks)
    second = merge_sequence(blocks)

    assert first == second
    assert first.block_count == 8
    assert len(finalize_value(first)) == 8


def test_attention_online_rejects_context_overflow() -> None:
    block = _stats(0)
    full = replace(block, block_count=16384)

    with pytest.raises(ValueError, match="exceeds"):
        merge_stats(full, block)


def test_attention_online_block_stats_use_complete_value_matrix() -> None:
    command = default_commands(1)[0]
    tensors = command_tensors(command)
    payload = producer_result(command)
    baseline = block_stats(payload["score_row"], payload["value_matrix"])
    changed_values = [list(row) for row in tensors["v"]]
    changed_values[-1][-1] += 1

    changed = block_stats(payload["score_row"], changed_values)

    assert changed.weighted_numerator[:-1] == baseline.weighted_numerator[:-1]
    assert changed.weighted_numerator[-1] != baseline.weighted_numerator[-1]


def test_attention_two_pass_is_order_invariant() -> None:
    payloads = [producer_result(command) for command in default_commands(8)]
    forward = two_pass_stats(
        [payload["score_row"] for payload in payloads],
        [payload["value_matrix"] for payload in payloads],
    )
    reverse = two_pass_stats(
        [payload["score_row"] for payload in reversed(payloads)],
        [payload["value_matrix"] for payload in reversed(payloads)],
    )

    assert forward == reverse
    assert finalize_value(forward) == finalize_value(reverse)


def test_attention_two_pass_score_buffer_fits_current_shared_sram() -> None:
    required = score_buffer_bytes(context_tokens=131072, attention_heads=32, score_bits=32)

    assert required == 16 * 1024 * 1024
    assert required < 68 * 1024 * 1024


def test_attention_two_pass_command_covers_all_blocks() -> None:
    command = default_commands(1)[0]

    result = two_pass_command(command, block_count=4)

    assert result["command_id"] == command.command_id
    assert result["block_count"] == 4
    assert result["exp_sum"] > 0
    assert len(result["value"]) == 8


def test_attention_two_pass_cycle_model_preserves_backpressured_commands() -> None:
    result = simulate_two_pass(
        default_commands(3),
        block_count=4,
        scenario="result_backpressure",
    )

    assert result["accepted_count"] == 3
    assert result["completed_count"] == 3
    assert [event["command_id"] for event in result["result_events"]] == [
        command.command_id for command in default_commands(3)
    ]
