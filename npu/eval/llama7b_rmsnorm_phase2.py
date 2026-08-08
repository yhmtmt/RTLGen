#!/usr/bin/env python3
"""Bit-exact Phase-2 finalization model for Llama-7B BF16 RMSNorm."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from npu.eval.llama7b_rmsnorm_reference import (
    CANONICAL_PROTOCOL_ERROR_BF16,
    HIDDEN_SIZE,
    _accumulate_squares,
    _has_exponent_255,
    _round_shift_right,
    _validate_inputs,
)


MANTISSA_FRACTION_BITS = 24
MANTISSA_WIDTH = 2 + MANTISSA_FRACTION_BITS
RSQRT_FRACTION_BITS = 20
RSQRT_WIDTH = 1 + RSQRT_FRACTION_BITS
SEED_ADDRESS_BITS = 8
SEED_RAW_ADDRESS_MIN = 1 << (SEED_ADDRESS_BITS - 2)
SEED_RAW_ADDRESS_MAX = (1 << SEED_ADDRESS_BITS) - 1
SEED_ROM_DEPTH = SEED_RAW_ADDRESS_MAX - SEED_RAW_ADDRESS_MIN + 1
NEWTON_ITERATIONS = 1
ONE_ITERATION_BIAS_Q20 = 4

EPSILON_COEFFICIENT = 1_099_512
EPSILON_EXPONENT = -40

FINALIZE_BASE_CYCLES = 2
NEWTON_CYCLES_PER_ITERATION = 3
OUTPUT_PIPELINE_LATENCY = 3

SEED_ROM_PATH = Path(__file__).resolve().parent / "data" / "llama7b_rmsnorm_rsqrt_seed_q20.hex"


@dataclass(frozen=True)
class RMSNormPhase2Metadata:
    lanes: int
    beats_per_row: int
    input_accept_cycles: int
    accumulation_replay_cycles: int
    finalize_cycles: int
    output_issue_cycles: int
    output_pipeline_latency: int
    no_stall_row_cycles: int
    seed_rom_reads: int
    newton_iterations: int
    newton_multiplications: int
    output_multiplications: int
    fixed_point_rne_boundaries: int
    bf16_narrow_boundaries: int


@dataclass(frozen=True)
class RMSNormPhase2Result:
    output: tuple[int, ...]
    protocol_error: bool
    accumulator_mantissa_48: int
    accumulator_lsb_exponent: int
    max_square_exponent: int
    variance_mantissa_q24: int
    variance_exponent_even: int
    seed_rom_address: int
    seed_q20: int
    rsqrt_mantissa_q20: int
    rsqrt_exponent: int
    metadata: RMSNormPhase2Metadata


def _rne_decimal_to_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_HALF_EVEN))


def generate_seed_rom_words() -> tuple[int, ...]:
    """Generate midpoint reciprocal-square-root seeds deterministically."""

    words = []
    address_scale = Decimal(1 << (SEED_ADDRESS_BITS - 2))
    output_scale = Decimal(1 << RSQRT_FRACTION_BITS)
    with localcontext() as context:
        context.prec = 80
        for raw_address in range(SEED_RAW_ADDRESS_MIN, SEED_RAW_ADDRESS_MAX + 1):
            midpoint = (Decimal(raw_address) + Decimal("0.5")) / address_scale
            seed = Decimal(1) / midpoint.sqrt()
            words.append(_rne_decimal_to_int(seed * output_scale))
    return tuple(words)


def seed_rom_text(words: Sequence[int] | None = None) -> str:
    selected = generate_seed_rom_words() if words is None else tuple(words)
    if len(selected) != SEED_ROM_DEPTH:
        raise ValueError(f"seed ROM must contain exactly {SEED_ROM_DEPTH} words")
    width_hex = (RSQRT_WIDTH + 3) // 4
    return "".join(f"{word:0{width_hex}x}\n" for word in selected)


def check_seed_rom(path: Path = SEED_ROM_PATH) -> None:
    expected = seed_rom_text()
    try:
        actual = path.read_text(encoding="ascii")
    except FileNotFoundError as exc:
        raise ValueError(f"missing RMSNorm seed ROM: {path}") from exc
    if actual != expected:
        raise ValueError(f"stale or malformed RMSNorm seed ROM: {path}")


@lru_cache(maxsize=1)
def load_seed_rom() -> tuple[int, ...]:
    check_seed_rom()
    return tuple(int(line, 16) for line in SEED_ROM_PATH.read_text(encoding="ascii").splitlines())


def _sum_power_terms(terms: Sequence[tuple[int, int]]) -> tuple[int, int]:
    nonzero = [(coefficient, exponent) for coefficient, exponent in terms if coefficient]
    if not nonzero:
        return 0, 0
    base_exponent = min(exponent for _, exponent in nonzero)
    total = sum(coefficient << (exponent - base_exponent) for coefficient, exponent in nonzero)
    return total, base_exponent


def _normalize_variance(accumulator: int, accumulator_lsb_exponent: int) -> tuple[int, int]:
    total, base_exponent = _sum_power_terms(
        (
            (accumulator, accumulator_lsb_exponent - 12),
            (EPSILON_COEFFICIENT, EPSILON_EXPONENT),
        )
    )
    leading_exponent = total.bit_length() - 1 + base_exponent
    even_exponent = leading_exponent if leading_exponent % 2 == 0 else leading_exponent - 1
    target_lsb_exponent = even_exponent - MANTISSA_FRACTION_BITS
    mantissa = _round_shift_right(total, target_lsb_exponent - base_exponent)
    if mantissa == (4 << MANTISSA_FRACTION_BITS):
        mantissa = 1 << MANTISSA_FRACTION_BITS
        even_exponent += 2
    if not (1 << MANTISSA_FRACTION_BITS) <= mantissa < (4 << MANTISSA_FRACTION_BITS):
        raise AssertionError("normalized RMSNorm variance outside Q2.24 range")
    return mantissa, even_exponent


def _saturate_unsigned(value: int, width: int) -> int:
    return min(max(value, 0), (1 << width) - 1)


def _seed_address(mantissa_q24: int) -> int:
    shift = MANTISSA_FRACTION_BITS - (SEED_ADDRESS_BITS - 2)
    raw_address = mantissa_q24 >> shift
    if not SEED_RAW_ADDRESS_MIN <= raw_address <= SEED_RAW_ADDRESS_MAX:
        raise AssertionError("normalized RMSNorm variance has invalid seed address")
    return raw_address - SEED_RAW_ADDRESS_MIN


def _newton_step(mantissa_q24: int, estimate_q20: int) -> int:
    estimate_square_q20 = _round_shift_right(
        estimate_q20 * estimate_q20,
        RSQRT_FRACTION_BITS,
    )
    half_m_estimate_square_q20 = _round_shift_right(
        mantissa_q24 * estimate_square_q20,
        MANTISSA_FRACTION_BITS + 1,
    )
    correction_q20 = 3 * (1 << (RSQRT_FRACTION_BITS - 1)) - half_m_estimate_square_q20
    if not 0 <= estimate_square_q20 < (1 << RSQRT_WIDTH):
        raise AssertionError("Newton y-square outside Q1.20 range")
    if not 0 <= half_m_estimate_square_q20 < (1 << (RSQRT_WIDTH + 1)):
        raise AssertionError("Newton half-m-y-square outside Q2.20 range")
    if not 0 <= correction_q20 < (1 << (RSQRT_WIDTH + 1)):
        raise AssertionError("Newton correction outside Q2.20 range")
    updated_q20 = _round_shift_right(
        estimate_q20 * correction_q20,
        RSQRT_FRACTION_BITS,
    )
    return _saturate_unsigned(updated_q20, RSQRT_WIDTH)


def reciprocal_sqrt_from_accumulator(
    accumulator: int,
    accumulator_lsb_exponent: int,
    *,
    iterations: int = NEWTON_ITERATIONS,
) -> tuple[int, int, int, int, int]:
    """Return normalized variance, seed metadata, and scaled Q1.20 rsqrt."""

    if iterations not in (1, 2):
        raise ValueError("iterations must be 1 or 2")
    mantissa_q24, even_exponent = _normalize_variance(accumulator, accumulator_lsb_exponent)
    address = _seed_address(mantissa_q24)
    seed_q20 = load_seed_rom()[address]
    estimate_q20 = seed_q20
    for _ in range(iterations):
        estimate_q20 = _newton_step(mantissa_q24, estimate_q20)
    if iterations == 1:
        estimate_q20 = _saturate_unsigned(estimate_q20 + ONE_ITERATION_BIAS_Q20, RSQRT_WIDTH)
    return mantissa_q24, even_exponent, address, seed_q20, estimate_q20


def _bf16_components(word: int) -> tuple[int, int, int]:
    sign = (word >> 15) & 1
    exponent_field = (word >> 7) & 0xFF
    fraction = word & 0x7F
    if exponent_field == 0:
        return sign, fraction, -133
    return sign, 128 + fraction, exponent_field - 134


def _round_exact_to_bf16(sign: int, coefficient: int, exponent: int) -> int:
    sign_word = sign << 15
    if coefficient == 0:
        return sign_word
    leading_exponent = coefficient.bit_length() - 1 + exponent
    if leading_exponent < -126:
        subnormal = _round_shift_right(coefficient, -133 - exponent)
        if subnormal < 128:
            return sign_word | subnormal
        return sign_word | 0x0080

    significand = _round_shift_right(coefficient, coefficient.bit_length() - 8)
    if significand == 256:
        significand = 128
        leading_exponent += 1
    if leading_exponent > 127:
        return sign_word | 0x7F80
    return sign_word | ((leading_exponent + 127) << 7) | (significand - 128)


def _scale_output_word(
    row_word: int,
    gamma_word: int,
    rsqrt_mantissa_q20: int,
    rsqrt_exponent: int,
) -> int:
    row_sign, row_significand, row_exponent = _bf16_components(row_word)
    gamma_sign, gamma_significand, gamma_exponent = _bf16_components(gamma_word)
    coefficient = row_significand * rsqrt_mantissa_q20 * gamma_significand
    exponent = row_exponent + gamma_exponent + rsqrt_exponent - RSQRT_FRACTION_BITS
    return _round_exact_to_bf16(row_sign ^ gamma_sign, coefficient, exponent)


def operation_metadata(lanes: int, *, iterations: int = NEWTON_ITERATIONS) -> RMSNormPhase2Metadata:
    if isinstance(lanes, bool) or not isinstance(lanes, int) or lanes <= 0 or HIDDEN_SIZE % lanes:
        raise ValueError(f"lanes must be a positive divisor of {HIDDEN_SIZE}")
    if iterations not in (1, 2):
        raise ValueError("iterations must be 1 or 2")
    beats = HIDDEN_SIZE // lanes
    finalize_cycles = FINALIZE_BASE_CYCLES + NEWTON_CYCLES_PER_ITERATION * iterations
    return RMSNormPhase2Metadata(
        lanes=lanes,
        beats_per_row=beats,
        input_accept_cycles=beats,
        accumulation_replay_cycles=beats,
        finalize_cycles=finalize_cycles,
        output_issue_cycles=beats,
        output_pipeline_latency=OUTPUT_PIPELINE_LATENCY,
        no_stall_row_cycles=3 * beats + finalize_cycles + OUTPUT_PIPELINE_LATENCY,
        seed_rom_reads=1,
        newton_iterations=iterations,
        newton_multiplications=3 * iterations,
        output_multiplications=2 * HIDDEN_SIZE,
        fixed_point_rne_boundaries=3 * iterations + 1,
        bf16_narrow_boundaries=HIDDEN_SIZE,
    )


def rmsnorm_bf16_phase2(
    row: Sequence[int],
    gamma: Sequence[int],
    *,
    lanes: int,
    iterations: int = NEWTON_ITERATIONS,
) -> RMSNormPhase2Result:
    """Evaluate one fixed-size row with the Phase-2 bit-exact contract."""

    _validate_inputs(row, gamma, lanes)
    metadata = operation_metadata(lanes, iterations=iterations)
    if _has_exponent_255(row) or _has_exponent_255(gamma):
        return RMSNormPhase2Result(
            output=(CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE,
            protocol_error=True,
            accumulator_mantissa_48=0,
            accumulator_lsb_exponent=0,
            max_square_exponent=0,
            variance_mantissa_q24=0,
            variance_exponent_even=0,
            seed_rom_address=0,
            seed_q20=0,
            rsqrt_mantissa_q20=0,
            rsqrt_exponent=0,
            metadata=metadata,
        )

    accumulator, lsb_exponent, max_square_exponent = _accumulate_squares(row)
    mantissa_q24, even_exponent, address, seed_q20, estimate_q20 = reciprocal_sqrt_from_accumulator(
        accumulator,
        lsb_exponent,
        iterations=iterations,
    )
    rsqrt_exponent = -(even_exponent // 2)
    output = tuple(
        _scale_output_word(value, weight, estimate_q20, rsqrt_exponent)
        for value, weight in zip(row, gamma)
    )
    return RMSNormPhase2Result(
        output=output,
        protocol_error=False,
        accumulator_mantissa_48=accumulator,
        accumulator_lsb_exponent=lsb_exponent,
        max_square_exponent=max_square_exponent,
        variance_mantissa_q24=mantissa_q24,
        variance_exponent_even=even_exponent,
        seed_rom_address=address,
        seed_q20=seed_q20,
        rsqrt_mantissa_q20=estimate_q20,
        rsqrt_exponent=rsqrt_exponent,
        metadata=metadata,
    )
