#!/usr/bin/env python3
"""Bit-exact BF16-boundary reference for Llama-7B transformer RMSNorm."""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Sequence


HIDDEN_SIZE = 4096
EPSILON = 1.0e-6
CANONICAL_PROTOCOL_ERROR_BF16 = 0x7FC0

_BF16_EXPONENT_MASK = 0x7F80
_FP32_ONE_BITS = 0x3F800000
_FP32_EPSILON_BITS = 0x358637BD


@dataclass(frozen=True)
class RMSNormResult:
    """One completed row and the arithmetic state exposed for RTL checking."""

    output: tuple[int, ...]
    protocol_error: bool
    sum_squares_fp32_bits: int
    mean_square_fp32_bits: int
    inv_rms_fp32_bits: int


def _bits_to_fp32(bits: int) -> float:
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def _fp32_to_bits(value: float) -> int:
    try:
        return struct.unpack(">I", struct.pack(">f", value))[0]
    except OverflowError:
        return 0xFF800000 if math.copysign(1.0, value) < 0.0 else 0x7F800000


def _round_fp32(value: float) -> float:
    return _bits_to_fp32(_fp32_to_bits(value))


def _add_fp32(lhs: float, rhs: float) -> float:
    return _round_fp32(lhs + rhs)


def _mul_fp32(lhs: float, rhs: float) -> float:
    return _round_fp32(lhs * rhs)


def _div_fp32(lhs: float, rhs: float) -> float:
    return _round_fp32(lhs / rhs)


def _sqrt_fp32(value: float) -> float:
    return _round_fp32(math.sqrt(value))


def bf16_to_fp32(word: int) -> float:
    """Decode one validated BF16 bit pattern exactly into an FP32 value."""

    _validate_word(word, name="BF16 word", index=None)
    return _bits_to_fp32(word << 16)


def fp32_to_bf16(value: float) -> int:
    """Round an FP32 value to BF16 using round-to-nearest, ties-to-even."""

    bits = _fp32_to_bits(value)
    exponent = (bits >> 23) & 0xFF
    fraction = bits & 0x7FFFFF
    if exponent == 0xFF:
        if fraction:
            return CANONICAL_PROTOCOL_ERROR_BF16
        return bits >> 16

    upper = bits >> 16
    discarded = bits & 0xFFFF
    if discarded > 0x8000 or (discarded == 0x8000 and (upper & 1)):
        upper += 1
    return upper & 0xFFFF


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


def rmsnorm_bf16(
    row: Sequence[int],
    gamma: Sequence[int],
    *,
    lanes: int,
) -> RMSNormResult:
    """Evaluate one fixed-size transformer RMSNorm row.

    ``lanes`` defines streaming beat width. Arithmetic always follows ascending
    logical element order, making the result invariant across legal lane counts.
    Inputs and outputs are raw BF16 words; all internal primitives are FP32 RNE.
    """

    _validate_inputs(row, gamma, lanes)
    if _has_exponent_255(row) or _has_exponent_255(gamma):
        return RMSNormResult(
            output=(CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE,
            protocol_error=True,
            sum_squares_fp32_bits=0,
            mean_square_fp32_bits=0,
            inv_rms_fp32_bits=0,
        )

    row_fp32 = tuple(_bits_to_fp32(word << 16) for word in row)
    gamma_fp32 = tuple(_bits_to_fp32(word << 16) for word in gamma)

    sum_squares = 0.0
    for beat_base in range(0, HIDDEN_SIZE, lanes):
        for lane in range(lanes):
            value = row_fp32[beat_base + lane]
            square = _mul_fp32(value, value)
            sum_squares = _add_fp32(sum_squares, square)

    # Division by 4096 is exact in binary before the explicit FP32 boundary.
    mean_square = _mul_fp32(sum_squares, _bits_to_fp32(0x39800000))
    variance_with_epsilon = _add_fp32(mean_square, _bits_to_fp32(_FP32_EPSILON_BITS))
    inv_rms = _div_fp32(_bits_to_fp32(_FP32_ONE_BITS), _sqrt_fp32(variance_with_epsilon))

    output = []
    for value, weight in zip(row_fp32, gamma_fp32):
        normalized = _mul_fp32(value, inv_rms)
        output.append(fp32_to_bf16(_mul_fp32(normalized, weight)))

    return RMSNormResult(
        output=tuple(output),
        protocol_error=False,
        sum_squares_fp32_bits=_fp32_to_bits(sum_squares),
        mean_square_fp32_bits=_fp32_to_bits(mean_square),
        inv_rms_fp32_bits=_fp32_to_bits(inv_rms),
    )
