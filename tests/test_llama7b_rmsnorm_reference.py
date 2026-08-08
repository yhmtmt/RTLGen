import math
import struct

import numpy as np
import pytest

from npu.eval.llama7b_rmsnorm_reference import (
    ACCUMULATOR_WIDTH,
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


def _decode_word(word: int) -> float:
    return float(struct.unpack(">f", struct.pack(">I", word << 16))[0])


def _decode(words: list[int] | tuple[int, ...]) -> np.ndarray:
    return np.asarray([_decode_word(word) for word in words], dtype=np.float64)


def _scaled_fp64_oracle(row: list[int], gamma: list[int]) -> np.ndarray:
    """Independent overflow-safe RMSNorm oracle with no model helper reuse."""

    x = [_decode_word(word) for word in row]
    weight = [_decode_word(word) for word in gamma]
    scale = max(abs(value) for value in x)
    if scale == 0.0:
        rms = math.sqrt(1.0e-6)
    else:
        scaled_mean_square = math.fsum((value / scale) ** 2 for value in x) / HIDDEN_SIZE
        rms = math.hypot(scale * math.sqrt(scaled_mean_square), math.sqrt(1.0e-6))
    return np.asarray([value / rms * gain for value, gain in zip(x, weight)], dtype=np.float64)


def test_matches_independent_scaled_fp64_oracle_and_is_lane_invariant() -> None:
    rng = np.random.default_rng(0x524D534E)
    row_values = rng.normal(0.0, 0.75, HIDDEN_SIZE).astype(np.float32)
    gamma_values = rng.uniform(0.5, 1.5, HIDDEN_SIZE).astype(np.float32)
    row = [_bf16(float(value)) for value in row_values]
    gamma = [_bf16(float(value)) for value in gamma_values]

    baseline = rmsnorm_bf16(row, gamma, lanes=1)
    assert not baseline.protocol_error
    for lanes in (2, 8, 16, 64, 256, 4096):
        assert rmsnorm_bf16(row, gamma, lanes=lanes) == baseline

    np.testing.assert_allclose(
        _decode(baseline.output),
        _scaled_fp64_oracle(row, gamma),
        rtol=8.0e-3,
        atol=2.0e-4,
    )


def test_uniform_row_has_pinned_bit_exact_accumulator_state() -> None:
    result = rmsnorm_bf16(
        [0x3F80] * HIDDEN_SIZE,
        [0x3F80] * HIDDEN_SIZE,
        lanes=16,
    )

    assert not result.protocol_error
    assert result.accumulator_mantissa_48 == 1 << 46
    assert result.accumulator_lsb_exponent == -34
    assert result.max_square_exponent == 0
    assert result.output == (0x3F80,) * HIDDEN_SIZE


def test_all_maximum_finite_normalizes_to_one_without_overflow() -> None:
    row = [0x7F7F] * HIDDEN_SIZE
    gamma = [0x3F80] * HIDDEN_SIZE

    result = rmsnorm_bf16(row, gamma, lanes=64)

    assert not result.protocol_error
    assert 0 < result.accumulator_mantissa_48 < (1 << ACCUMULATOR_WIDTH)
    assert result.accumulator_lsb_exponent == 221
    assert result.max_square_exponent == 255
    assert result.output == (0x3F80,) * HIDDEN_SIZE
    np.testing.assert_allclose(
        _decode(result.output),
        _scaled_fp64_oracle(row, gamma),
        rtol=8.0e-3,
        atol=0.0,
    )


def test_mixed_exponents_are_order_and_lane_invariant() -> None:
    pattern = [
        0x0001,
        0x807F,
        _bf16(2.0**-100),
        _bf16(-(2.0**-40)),
        _bf16(2.0**-10),
        _bf16(-1.0),
        _bf16(2.0**20),
        _bf16(-(2.0**60)),
        0x7F7F,
    ]
    row = [pattern[index % len(pattern)] for index in range(HIDDEN_SIZE)]
    gamma = [_bf16(0.5 + (index % 5) * 0.25) for index in range(HIDDEN_SIZE)]
    baseline = rmsnorm_bf16(row, gamma, lanes=1)

    permutation = np.random.default_rng(0xB10CF10A).permutation(HIDDEN_SIZE).tolist()
    shuffled_row = [row[index] for index in permutation]
    shuffled_gamma = [gamma[index] for index in permutation]
    shuffled = rmsnorm_bf16(shuffled_row, shuffled_gamma, lanes=128)

    assert shuffled.accumulator_mantissa_48 == baseline.accumulator_mantissa_48
    assert shuffled.accumulator_lsb_exponent == baseline.accumulator_lsb_exponent
    assert shuffled.max_square_exponent == baseline.max_square_exponent
    assert shuffled.output == tuple(baseline.output[index] for index in permutation)
    for lanes in (4, 16, 64, 1024):
        assert rmsnorm_bf16(row, gamma, lanes=lanes) == baseline


def test_every_finite_exponent_class_stays_within_accumulator_bound() -> None:
    row = []
    for index in range(HIDDEN_SIZE):
        exponent = index % 255
        fraction = (index * 73) & 0x7F
        sign = (index & 1) << 15
        row.append(sign | (exponent << 7) | fraction)

    result = rmsnorm_bf16(row, [0x3F80] * HIDDEN_SIZE, lanes=32)

    assert not result.protocol_error
    assert 0 < result.accumulator_mantissa_48 < (1 << ACCUMULATOR_WIDTH)
    np.testing.assert_allclose(
        _decode(result.output),
        _scaled_fp64_oracle(row, [0x3F80] * HIDDEN_SIZE),
        rtol=8.0e-3,
        atol=1.0e-40,
    )


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
    assert result.accumulator_lsb_exponent == -298
    assert result.max_square_exponent == -264
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
    assert result.accumulator_mantissa_48 == 0
    assert result.accumulator_lsb_exponent == 0
    assert result.max_square_exponent == 0
    assert result.provisional_inv_rms == 0.0


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
