#!/usr/bin/env python3
"""Phase-1 BF16-boundary reference for Llama-7B transformer RMSNorm."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Sequence


HIDDEN_SIZE = 4096
EPSILON = 1.0e-6
ACCUMULATOR_WIDTH = 48
ACCUMULATOR_TERM_MSB = 34
CANONICAL_PROTOCOL_ERROR_BF16 = 0x7FC0

_BF16_EXPONENT_MASK = 0x7F80


@dataclass(frozen=True)
class RMSNormResult:
    """Completed row, bit-exact accumulation state, and provisional finalization."""

    output: tuple[int, ...]
    protocol_error: bool
    accumulator_mantissa_48: int
    accumulator_lsb_exponent: int
    max_square_exponent: int
    provisional_inv_rms: float


def _bits_to_fp32(bits: int) -> float:
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def _fp32_to_bits(value: float) -> int:
    try:
        return struct.unpack(">I", struct.pack(">f", value))[0]
    except OverflowError:
        return 0xFF800000 if math.copysign(1.0, value) < 0.0 else 0x7F800000


def bf16_to_fp32(word: int) -> float:
    """Decode one validated BF16 bit pattern exactly into an FP32 value."""

    _validate_word(word, name="BF16 word", index=None)
    return _bits_to_fp32(word << 16)


def _round_ratio_pow2(numerator: int, denominator: int, shift: int) -> int:
    if shift >= 0:
        numerator <<= shift
    else:
        denominator <<= -shift
    quotient, remainder = divmod(numerator, denominator)
    twice_remainder = remainder << 1
    if twice_remainder > denominator or (twice_remainder == denominator and (quotient & 1)):
        quotient += 1
    return quotient


def _float64_to_bf16(value: float) -> int:
    """Round binary64 directly to BF16 RNE without an FP32 double-round."""

    sign = 0x8000 if math.copysign(1.0, value) < 0.0 else 0
    magnitude = abs(value)
    if math.isnan(magnitude):
        return CANONICAL_PROTOCOL_ERROR_BF16
    if math.isinf(magnitude):
        return sign | 0x7F80
    if magnitude == 0.0:
        return sign

    numerator, denominator = magnitude.as_integer_ratio()
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < (denominator << exponent):
            exponent -= 1
    elif (numerator << -exponent) < denominator:
        exponent -= 1

    if exponent < -126:
        significand = _round_ratio_pow2(numerator, denominator, 133)
        if significand < 128:
            return sign | significand
        return sign | 0x0080

    significand = _round_ratio_pow2(numerator, denominator, 7 - exponent)
    if significand == 256:
        significand = 128
        exponent += 1
    if exponent > 127:
        return sign | 0x7F80
    return sign | ((exponent + 127) << 7) | (significand - 128)


def fp32_to_bf16(value: float) -> int:
    """Round an FP32 value to BF16 RNE, canonicalizing an FP32 NaN."""

    return _float64_to_bf16(_bits_to_fp32(_fp32_to_bits(value)))


def _validate_word(word: int, *, name: str, index: int | None) -> None:
    location = "" if index is None else f"[{index}]"
    if isinstance(word, bool) or not isinstance(word, int) or not 0 <= word <= 0xFFFF:
        raise ValueError(f"{name}{location} must be an integer BF16 word in [0, 0xffff]")


def _validate_inputs(row: Sequence[int], gamma: Sequence[int], lanes: int) -> None:
    if len(row) != HIDDEN_SIZE:
        raise ValueError(f"row must contain exactly {HIDDEN_SIZE} BF16 words")
    if len(gamma) != HIDDEN_SIZE:
        raise ValueError(f"gamma must contain exactly {HIDDEN_SIZE} BF16 words")
    if isinstance(lanes, bool) or not isinstance(lanes, int) or lanes <= 0:
        raise ValueError("lanes must be a positive integer")
    if HIDDEN_SIZE % lanes:
        raise ValueError(f"lanes must divide hidden size {HIDDEN_SIZE}")
    for index, word in enumerate(row):
        _validate_word(word, name="row", index=index)
    for index, word in enumerate(gamma):
        _validate_word(word, name="gamma", index=index)


def _has_exponent_255(words: Sequence[int]) -> bool:
    return any((word & _BF16_EXPONENT_MASK) == _BF16_EXPONENT_MASK for word in words)


def _square_components(word: int) -> tuple[int, int]:
    """Return exact square as ``coefficient * 2**exponent``."""

    exponent_field = (word >> 7) & 0xFF
    fraction = word & 0x7F
    if exponent_field == 0:
        significand = fraction
        value_exponent = -133
    else:
        significand = 128 + fraction
        value_exponent = exponent_field - 134
    return significand * significand, 2 * value_exponent


def _round_shift_right(value: int, shift: int) -> int:
    if shift <= 0:
        return value << -shift
    quotient = value >> shift
    remainder = value - (quotient << shift)
    halfway = 1 << (shift - 1)
    if remainder > halfway or (remainder == halfway and (quotient & 1)):
        quotient += 1
    return quotient


def _accumulate_squares(row: Sequence[int]) -> tuple[int, int, int]:
    terms = [_square_components(word) for word in row]
    nonzero_terms = [(coefficient, exponent) for coefficient, exponent in terms if coefficient]
    if not nonzero_terms:
        return 0, 0, 0

    max_square_exponent = max(coefficient.bit_length() - 1 + exponent for coefficient, exponent in nonzero_terms)
    accumulator_lsb_exponent = max_square_exponent - ACCUMULATOR_TERM_MSB
    accumulator = 0
    for coefficient, exponent in terms:
        accumulator += _round_shift_right(coefficient, accumulator_lsb_exponent - exponent)

    if accumulator >= (1 << ACCUMULATOR_WIDTH):
        raise AssertionError("48-bit RMSNorm accumulator bound violated")
    return accumulator, accumulator_lsb_exponent, max_square_exponent


def rmsnorm_bf16(
    row: Sequence[int],
    gamma: Sequence[int],
    *,
    lanes: int,
) -> RMSNormResult:
    """Evaluate one fixed-size transformer RMSNorm row.

    The block-floating accumulation fields are bit-exact Phase-1 contract state.
    Reciprocal square root, multiplication, and BF16 output are provisional
    correctly-scaled software semantics pending a Phase-2 approximation freeze.
    """

    _validate_inputs(row, gamma, lanes)
    if _has_exponent_255(row) or _has_exponent_255(gamma):
        return RMSNormResult(
            output=(CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE,
            protocol_error=True,
            accumulator_mantissa_48=0,
            accumulator_lsb_exponent=0,
            max_square_exponent=0,
            provisional_inv_rms=0.0,
        )

    accumulator, lsb_exponent, max_square_exponent = _accumulate_squares(row)
    mean_square = math.ldexp(float(accumulator), lsb_exponent - 12)
    provisional_inv_rms = 1.0 / math.sqrt(mean_square + EPSILON)

    output = tuple(
        _float64_to_bf16(bf16_to_fp32(value) * provisional_inv_rms * bf16_to_fp32(weight))
        for value, weight in zip(row, gamma)
    )
    return RMSNormResult(
        output=output,
        protocol_error=False,
        accumulator_mantissa_48=accumulator,
        accumulator_lsb_exponent=lsb_exponent,
        max_square_exponent=max_square_exponent,
        provisional_inv_rms=provisional_inv_rms,
    )
