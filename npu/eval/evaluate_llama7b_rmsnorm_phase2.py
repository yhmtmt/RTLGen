#!/usr/bin/env python3
"""Evaluate Phase-2 RMSNorm candidates against a robust scaled FP64 oracle."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
from typing import Any, Sequence

import numpy as np

from npu.eval.llama7b_rmsnorm_phase2 import (
    EPSILON_COEFFICIENT,
    EPSILON_EXPONENT,
    HIDDEN_SIZE,
    MANTISSA_FRACTION_BITS,
    NEWTON_ITERATIONS,
    ONE_ITERATION_BIAS_Q20,
    RSQRT_FRACTION_BITS,
    SEED_ROM_DEPTH,
    rmsnorm_bf16_phase2,
)


JsonDict = dict[str, Any]


def _bf16_from_fp32(value: float) -> int:
    bits = struct.unpack(">I", struct.pack(">f", value))[0]
    upper, lower = bits >> 16, bits & 0xFFFF
    if lower > 0x8000 or (lower == 0x8000 and (upper & 1)):
        upper += 1
    return upper & 0xFFFF


def _decode_bf16(word: int) -> float:
    return float(struct.unpack(">f", struct.pack(">I", word << 16))[0])


def _round_ratio_pow2(numerator: int, denominator: int, shift: int) -> int:
    if shift >= 0:
        numerator <<= shift
    else:
        denominator <<= -shift
    quotient, remainder = divmod(numerator, denominator)
    doubled = remainder << 1
    if doubled > denominator or (doubled == denominator and (quotient & 1)):
        quotient += 1
    return quotient


def _oracle_bf16(value: float) -> int:
    sign = 0x8000 if math.copysign(1.0, value) < 0.0 else 0
    magnitude = abs(value)
    if math.isinf(magnitude):
        return sign | 0x7F80
    if magnitude == 0.0:
        return sign
    numerator, denominator = magnitude.as_integer_ratio()
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < denominator << exponent:
            exponent -= 1
    elif numerator << -exponent < denominator:
        exponent -= 1
    if exponent < -126:
        significand = _round_ratio_pow2(numerator, denominator, 133)
        return sign | (significand if significand < 128 else 0x0080)
    significand = _round_ratio_pow2(numerator, denominator, 7 - exponent)
    if significand == 256:
        significand = 128
        exponent += 1
    if exponent > 127:
        return sign | 0x7F80
    return sign | ((exponent + 127) << 7) | (significand - 128)


def _ordered_bf16(word: int) -> int:
    return ((~word) & 0xFFFF) if word & 0x8000 else (word | 0x8000)


def _scaled_oracle(row: Sequence[int], gamma: Sequence[int]) -> tuple[float, tuple[int, ...]]:
    x = [_decode_bf16(word) for word in row]
    weights = [_decode_bf16(word) for word in gamma]
    scale = max(abs(value) for value in x)
    if scale == 0.0:
        rms = math.sqrt(1.0e-6)
    else:
        scaled_mean = math.fsum((value / scale) ** 2 for value in x) / HIDDEN_SIZE
        rms = math.hypot(scale * math.sqrt(scaled_mean), math.sqrt(1.0e-6))
    inv_rms = 1.0 / rms
    return inv_rms, tuple(_oracle_bf16(value * inv_rms * weight) for value, weight in zip(x, weights))


def _normal_row(rng: np.random.Generator, *, scale: float) -> tuple[list[int], list[int]]:
    values = rng.normal(0.0, scale, HIDDEN_SIZE).astype(np.float32)
    gains = np.clip(rng.normal(1.0, 0.12, HIDDEN_SIZE), 0.5, 1.5).astype(np.float32)
    return ([_bf16_from_fp32(float(value)) for value in values], [_bf16_from_fp32(float(gain)) for gain in gains])


def _random_log_row(rng: np.random.Generator) -> tuple[list[int], list[int]]:
    exponents = rng.integers(-16, 17, size=HIDDEN_SIZE)
    mantissas = rng.uniform(1.0, 2.0, size=HIDDEN_SIZE)
    signs = rng.choice(np.asarray([-1.0, 1.0]), size=HIDDEN_SIZE)
    values = signs * mantissas * np.exp2(exponents)
    gains = rng.uniform(0.5, 1.5, size=HIDDEN_SIZE)
    return ([_bf16_from_fp32(float(value)) for value in values], [_bf16_from_fp32(float(gain)) for gain in gains])


def representative_cases() -> list[tuple[str, str, list[int], list[int]]]:
    rng = np.random.default_rng(0x4C4C414D413742)
    cases = []
    for index, scale in enumerate((0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0) * 2):
        row, gamma = _normal_row(rng, scale=scale)
        cases.append(("representative", f"llama_like_{index:02d}", row, gamma))
    for index in range(12):
        row, gamma = _random_log_row(rng)
        cases.append(("representative", f"random_log_{index:02d}", row, gamma))
    return cases


def adversarial_cases() -> list[tuple[str, str, list[int], list[int]]]:
    ones = [0x3F80] * HIDDEN_SIZE
    cases = [
        ("adversarial", "positive_zero", [0x0000] * HIDDEN_SIZE, ones),
        ("adversarial", "negative_zero", [0x8000] * HIDDEN_SIZE, ones),
        ("adversarial", "minimum_subnormal", [0x0001] * HIDDEN_SIZE, ones),
        ("adversarial", "maximum_finite", [0x7F7F] * HIDDEN_SIZE, ones),
        ("adversarial", "alternating_max", [0x7F7F, 0xFF7F] * (HIDDEN_SIZE // 2), ones),
        ("adversarial", "one_maximum", [0x7F7F] + [0x0000] * (HIDDEN_SIZE - 1), ones),
        ("adversarial", "one_subnormal", [0x0001] + [0x0000] * (HIDDEN_SIZE - 1), ones),
    ]
    for index, value in enumerate((2.0**-20, 2.0**-10, 9.765625e-4, 2.0**-5, 1.0, 32.0, 2.0**60)):
        word = _bf16_from_fp32(value)
        row = [word if lane % 3 else (word | 0x8000) for lane in range(HIDDEN_SIZE)]
        cases.append(("adversarial", f"uniform_scale_{index:02d}", row, ones))

    exponent_sweep = []
    for index in range(HIDDEN_SIZE):
        exponent = index % 255
        fraction = (index * 73) & 0x7F
        exponent_sweep.append(((index & 1) << 15) | (exponent << 7) | fraction)
    cases.append(("adversarial", "all_finite_exponents", exponent_sweep, ones))

    mixed = [0x0001, 0x807F, 0x2F80, 0xBF80, 0x4F00, 0xDF00, 0x7F7F]
    mixed_row = [mixed[index % len(mixed)] for index in range(HIDDEN_SIZE)]
    mixed_gamma = [_bf16_from_fp32(0.5 + (index % 5) * 0.25) for index in range(HIDDEN_SIZE)]
    cases.append(("adversarial", "mixed_extremes", mixed_row, mixed_gamma))

    rng = np.random.default_rng(0x4144564552534152)
    for index, exponent in enumerate((-120, -80, -40, -20, 20, 60, 100, 120)):
        scale = math.ldexp(1.0, exponent)
        values = rng.uniform(-1.75, 1.75, HIDDEN_SIZE) * scale
        gains = np.exp2(rng.uniform(-3.0, 3.0, HIDDEN_SIZE))
        row = [_bf16_from_fp32(float(value)) for value in values]
        gamma = [_bf16_from_fp32(float(gain)) for gain in gains]
        cases.append(("adversarial", f"broad_exponent_{index:02d}", row, gamma))

    for active in (1, 3, 17, 255, 2047):
        row = [0x0000] * HIDDEN_SIZE
        for index in range(active):
            magnitude = _bf16_from_fp32(1.0 + (index % 31) / 32.0)
            row[(index * 2053) % HIDDEN_SIZE] = magnitude | ((index & 1) << 15)
        gamma = [_bf16_from_fp32(0.25 + (index % 29) / 8.0) for index in range(HIDDEN_SIZE)]
        cases.append(("adversarial", f"sparse_{active:04d}", row, gamma))
    return cases


def _candidate_report(iterations: int) -> JsonDict:
    category_stats: dict[str, JsonDict] = {}
    row_relative_errors = []
    signed_ulp_errors = []
    for category, name, row, gamma in representative_cases() + adversarial_cases():
        result = rmsnorm_bf16_phase2(row, gamma, lanes=16, iterations=iterations)
        oracle_inv_rms, oracle_output = _scaled_oracle(row, gamma)
        model_inv_rms = math.ldexp(
            result.rsqrt_mantissa_q20 / float(1 << RSQRT_FRACTION_BITS),
            result.rsqrt_exponent,
        )
        relative_error = model_inv_rms / oracle_inv_rms - 1.0
        row_relative_errors.append(relative_error)
        ulp_errors = [
            _ordered_bf16(actual) - _ordered_bf16(expected)
            for actual, expected in zip(result.output, oracle_output)
        ]
        signed_ulp_errors.extend(ulp_errors)
        stats = category_stats.setdefault(
            category,
            {"rows": 0, "outputs": 0, "exact": 0, "within_1_ulp": 0, "within_2_ulp": 0, "max_ulp": 0, "worst_case": ""},
        )
        absolute = [abs(error) for error in ulp_errors]
        case_max = max(absolute)
        stats["rows"] += 1
        stats["outputs"] += HIDDEN_SIZE
        stats["exact"] += sum(error == 0 for error in absolute)
        stats["within_1_ulp"] += sum(error <= 1 for error in absolute)
        stats["within_2_ulp"] += sum(error <= 2 for error in absolute)
        if case_max > stats["max_ulp"]:
            stats["max_ulp"] = case_max
            stats["worst_case"] = name

    for stats in category_stats.values():
        outputs = stats["outputs"]
        stats["exact_rate"] = stats["exact"] / outputs
        stats["within_1_ulp_rate"] = stats["within_1_ulp"] / outputs
        stats["within_2_ulp_rate"] = stats["within_2_ulp"] / outputs
    return {
        "iterations": iterations,
        "categories": category_stats,
        "rsqrt_relative_error": {
            "mean": math.fsum(row_relative_errors) / len(row_relative_errors),
            "max_abs": max(abs(error) for error in row_relative_errors),
            "negative_rows": sum(error < 0.0 for error in row_relative_errors),
            "positive_rows": sum(error > 0.0 for error in row_relative_errors),
            "zero_rows": sum(error == 0.0 for error in row_relative_errors),
        },
        "output_signed_ulp_mean": math.fsum(signed_ulp_errors) / len(signed_ulp_errors),
    }


def build_report() -> JsonDict:
    candidates = [_candidate_report(iterations) for iterations in (1, 2)]
    passing = [
        candidate
        for candidate in candidates
        if candidate["categories"]["representative"]["max_ulp"] <= 1
        and candidate["categories"]["adversarial"]["max_ulp"] <= 2
        and abs(candidate["rsqrt_relative_error"]["mean"]) <= 1.0e-5
        and abs(candidate["output_signed_ulp_mean"]) <= 1.0e-3
    ]
    if not passing:
        raise AssertionError("no Phase-2 RMSNorm candidate meets the numerical gates")
    chosen = min(passing, key=lambda candidate: candidate["iterations"])
    return {
        "contract": "llama7b_rmsnorm_bf16_phase2_v1",
        "formats": {
            "variance_mantissa": f"Q2.{MANTISSA_FRACTION_BITS}",
            "seed_and_rsqrt": f"Q1.{RSQRT_FRACTION_BITS}",
            "seed_rom_entries": SEED_ROM_DEPTH,
            "epsilon": f"{EPSILON_COEFFICIENT} * 2^{EPSILON_EXPONENT}",
            "one_iteration_bias_q20": ONE_ITERATION_BIAS_Q20,
        },
        "candidates": candidates,
        "chosen_iterations": chosen["iterations"],
        "configured_iterations": NEWTON_ITERATIONS,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
