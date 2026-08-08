import math
import struct

import numpy as np
import pytest

from npu.eval.llama7b_rmsnorm_reference import (
    CANONICAL_PROTOCOL_ERROR_BF16,
    HIDDEN_SIZE,
    bf16_to_fp32,
    fp32_to_bf16,
    rmsnorm_bf16,
)


def _bf16(value: float) -> int:
    bits = struct.unpack(">I", struct.pack(">f", value))[0]
    upper, lower = bits >> 16, bits & 0xFFFF
    return (upper + (lower > 0x8000 or (lower == 0x8000 and (upper & 1)))) & 0xFFFF


def _decode(words: list[int] | tuple[int, ...]) -> np.ndarray:
    bits = np.asarray(words, dtype=np.uint16).astype(np.uint32) << 16
    return bits.view(np.float32)


def _oracle(row: list[int], gamma: list[int]) -> np.ndarray:
    x = _decode(row)
    weight = _decode(gamma)
    mean_square = np.mean(x * x, dtype=np.float32)
    inv_rms = np.float32(1.0) / np.sqrt(mean_square + np.float32(1.0e-6), dtype=np.float32)
    return np.asarray(x * inv_rms * weight, dtype=np.float32)


def test_matches_independent_fp32_oracle_and_is_lane_invariant() -> None:
    rng = np.random.default_rng(0x524D534E)
    row_values = rng.normal(0.0, 0.75, HIDDEN_SIZE).astype(np.float32)
    gamma_values = rng.uniform(0.5, 1.5, HIDDEN_SIZE).astype(np.float32)
    row = [_bf16(float(value)) for value in row_values]
    gamma = [_bf16(float(value)) for value in gamma_values]

    baseline = rmsnorm_bf16(row, gamma, lanes=1)
    assert not baseline.protocol_error
    for lanes in (2, 8, 16, 64, 256, 4096):
        assert rmsnorm_bf16(row, gamma, lanes=lanes) == baseline

    actual = _decode(baseline.output)
    expected = _oracle(row, gamma)
    np.testing.assert_allclose(actual, expected, rtol=8.0e-3, atol=2.0e-4)


def test_uniform_row_has_pinned_bit_exact_arithmetic_state() -> None:
    result = rmsnorm_bf16(
        [0x3F80] * HIDDEN_SIZE,
        [0x3F80] * HIDDEN_SIZE,
        lanes=16,
    )

    assert not result.protocol_error
    assert result.sum_squares_fp32_bits == 0x45800000
    assert result.mean_square_fp32_bits == 0x3F800000
    assert result.inv_rms_fp32_bits == 0x3F7FFFF8
    assert result.output == (0x3F80,) * HIDDEN_SIZE


def test_adversarial_dynamic_range_tracks_fp32_oracle() -> None:
    pattern = [
        0x0001,
        0x8001,
        _bf16(2.0**-60),
        _bf16(-(2.0**-30)),
        _bf16(1.0),
        _bf16(-1.0),
        _bf16(127.5),
        _bf16(-255.0),
    ]
    row = (pattern * (HIDDEN_SIZE // len(pattern)))[:HIDDEN_SIZE]
    gamma = ([_bf16(0.5), _bf16(-0.75), _bf16(1.0), _bf16(1.5)] * 1024)[:HIDDEN_SIZE]

    result = rmsnorm_bf16(row, gamma, lanes=32)
    assert not result.protocol_error
    np.testing.assert_allclose(
        _decode(result.output),
        _oracle(row, gamma),
        rtol=8.0e-3,
        atol=2.0e-4,
    )


def test_finite_fp32_overflow_is_not_an_input_protocol_error() -> None:
    result = rmsnorm_bf16(
        [0x7F7F] * HIDDEN_SIZE,
        [0x3F80] * HIDDEN_SIZE,
        lanes=64,
    )

    assert not result.protocol_error
    assert result.sum_squares_fp32_bits == 0x7F800000
    assert result.mean_square_fp32_bits == 0x7F800000
    assert result.inv_rms_fp32_bits == 0x00000000
    assert result.output == (0x0000,) * HIDDEN_SIZE


def test_subnormals_and_signed_zero_are_not_flushed_on_input() -> None:
    row = [0x0000] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    row[:6] = [0x0000, 0x8000, 0x0001, 0x8001, 0x0002, 0x8002]
    gamma[:6] = [0x3F80, 0x3F80, 0xBF80, 0xBF80, 0x8000, 0x0000]

    result = rmsnorm_bf16(row, gamma, lanes=16)

    assert result.output[0] == 0x0000
    assert result.output[1] == 0x8000
    assert result.output[2] != 0 and result.output[2] & 0x8000
    assert result.output[3] != 0 and not result.output[3] & 0x8000
    assert result.output[4] == 0x8000
    assert result.output[5] == 0x8000
    assert bf16_to_fp32(0x0001) == math.ldexp(1.0, -133)
    assert math.copysign(1.0, bf16_to_fp32(0x8000)) < 0.0


@pytest.mark.parametrize("bad_word", [0x7F80, 0xFF80, 0x7F81, 0xFFC1])
@pytest.mark.parametrize("target", ["row", "gamma"])
def test_exponent_255_input_has_canonical_protocol_error(bad_word: int, target: str) -> None:
    row = [0x3F80] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE
    (row if target == "row" else gamma)[HIDDEN_SIZE - 1] = bad_word

    result = rmsnorm_bf16(row, gamma, lanes=16)

    assert result.protocol_error
    assert result.output == (CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE
    assert result.sum_squares_fp32_bits == 0
    assert result.mean_square_fp32_bits == 0
    assert result.inv_rms_fp32_bits == 0


@pytest.mark.parametrize(
    ("row_size", "gamma_size", "lanes"),
    [
        (HIDDEN_SIZE - 1, HIDDEN_SIZE, 16),
        (HIDDEN_SIZE + 1, HIDDEN_SIZE, 16),
        (HIDDEN_SIZE, HIDDEN_SIZE - 1, 16),
        (HIDDEN_SIZE, HIDDEN_SIZE + 1, 16),
        (HIDDEN_SIZE, HIDDEN_SIZE, 0),
        (HIDDEN_SIZE, HIDDEN_SIZE, 3),
    ],
)
def test_malformed_dimensions_fail_closed(row_size: int, gamma_size: int, lanes: int) -> None:
    with pytest.raises(ValueError):
        rmsnorm_bf16([0] * row_size, [0x3F80] * gamma_size, lanes=lanes)


@pytest.mark.parametrize("bad_word", [-1, 0x10000, 1.0, True])
def test_malformed_words_fail_closed(bad_word: object) -> None:
    row = [0] * HIDDEN_SIZE
    row[2048] = bad_word  # type: ignore[assignment]
    with pytest.raises(ValueError):
        rmsnorm_bf16(row, [0x3F80] * HIDDEN_SIZE, lanes=16)


def test_fp32_to_bf16_uses_ties_to_even_and_preserves_zero_sign() -> None:
    even_halfway = struct.unpack(">f", struct.pack(">I", 0x3F808000))[0]
    odd_halfway = struct.unpack(">f", struct.pack(">I", 0x3F818000))[0]
    assert fp32_to_bf16(even_halfway) == 0x3F80
    assert fp32_to_bf16(odd_halfway) == 0x3F82
    assert fp32_to_bf16(-0.0) == 0x8000
