import json
from pathlib import Path

import pytest

from npu.eval.evaluate_llama7b_rmsnorm_phase2 import build_report
from npu.eval.llama7b_rmsnorm_phase2 import (
    CANONICAL_PROTOCOL_ERROR_BF16,
    HIDDEN_SIZE,
    NEWTON_ITERATIONS,
    RSQRT_FRACTION_BITS,
    SEED_ROM_DEPTH,
    _round_exact_to_bf16,
    check_seed_rom,
    generate_seed_rom_words,
    operation_metadata,
    rmsnorm_bf16_phase2,
    seed_rom_text,
)

def test_seed_rom_is_generated_checked_and_monotonic() -> None:
    words = generate_seed_rom_words()

    assert len(words) == SEED_ROM_DEPTH == 192
    assert all(0 < word < (1 << RSQRT_FRACTION_BITS) for word in words)
    assert all(lhs >= rhs for lhs, rhs in zip(words, words[1:]))
    check_seed_rom()


def test_seed_rom_guard_rejects_stale_content(tmp_path: Path) -> None:
    stale = tmp_path / "seed.hex"
    stale.write_text(seed_rom_text().replace("\n", "\n", 1) + "000000\n", encoding="ascii")
    with pytest.raises(ValueError, match="stale or malformed"):
        check_seed_rom(stale)


def test_checked_evaluation_report_matches_deterministic_sweep() -> None:
    report_path = Path(__file__).resolve().parents[1] / "docs" / "reference" / "llama7b_rmsnorm_phase2_evaluation.json"
    checked = json.loads(report_path.read_text(encoding="utf-8"))
    assert checked == build_report()


def test_unity_row_pins_phase2_internal_state() -> None:
    result = rmsnorm_bf16_phase2(
        [0x3F80] * HIDDEN_SIZE,
        [0x3F80] * HIDDEN_SIZE,
        lanes=16,
    )

    assert not result.protocol_error
    assert result.accumulator_mantissa_48 == 1 << 46
    assert result.accumulator_lsb_exponent == -34
    assert result.variance_mantissa_q24 == 16_777_233
    assert result.variance_exponent_even == 0
    assert result.seed_rom_address == 0
    assert result.seed_q20 == 1_044_504
    assert result.rsqrt_mantissa_q20 == 1_048_555
    assert result.rsqrt_exponent == 0
    assert result.output == (0x3F80,) * HIDDEN_SIZE


def test_maximum_finite_and_subnormal_rows_are_correctly_scaled() -> None:
    gamma = [0x3F80] * HIDDEN_SIZE
    maximum = rmsnorm_bf16_phase2([0x7F7F] * HIDDEN_SIZE, gamma, lanes=64)
    subnormal = rmsnorm_bf16_phase2([0x0001] * HIDDEN_SIZE, gamma, lanes=64)

    assert not maximum.protocol_error
    assert maximum.output == (0x3F80,) * HIDDEN_SIZE
    assert maximum.variance_exponent_even == 254
    assert maximum.rsqrt_exponent == -127
    assert not subnormal.protocol_error
    assert subnormal.output == (0x01FA,) * HIDDEN_SIZE
    assert subnormal.variance_exponent_even == -20
    assert subnormal.rsqrt_exponent == 10


def test_signed_zero_and_exponent_255_protocol_behavior() -> None:
    gamma = [0x3F80] * HIDDEN_SIZE
    zeros = rmsnorm_bf16_phase2([0x8000] * HIDDEN_SIZE, gamma, lanes=16)
    assert zeros.output == (0x8000,) * HIDDEN_SIZE

    row = [0x3F80] * HIDDEN_SIZE
    row[-1] = 0x7F80
    error = rmsnorm_bf16_phase2(row, gamma, lanes=16)
    assert error.protocol_error
    assert error.output == (CANONICAL_PROTOCOL_ERROR_BF16,) * HIDDEN_SIZE
    assert error.accumulator_mantissa_48 == 0
    assert error.rsqrt_mantissa_q20 == 0


def test_numerical_state_is_lane_invariant() -> None:
    pattern = [0x0001, 0x807F, 0x2F80, 0xBF80, 0x4F00, 0xDF00, 0x7F7F]
    row = [pattern[index % len(pattern)] for index in range(HIDDEN_SIZE)]
    gamma = [0x3F00 + (index % 5) * 0x20 for index in range(HIDDEN_SIZE)]
    baseline = rmsnorm_bf16_phase2(row, gamma, lanes=1)

    for lanes in (8, 16, 64, 256, 4096):
        candidate = rmsnorm_bf16_phase2(row, gamma, lanes=lanes)
        assert candidate.output == baseline.output
        assert candidate.accumulator_mantissa_48 == baseline.accumulator_mantissa_48
        assert candidate.accumulator_lsb_exponent == baseline.accumulator_lsb_exponent
        assert candidate.variance_mantissa_q24 == baseline.variance_mantissa_q24
        assert candidate.rsqrt_mantissa_q20 == baseline.rsqrt_mantissa_q20


def test_one_iteration_is_selected_by_measured_ulp_gates() -> None:
    report = build_report()
    candidates = {candidate["iterations"]: candidate for candidate in report["candidates"]}

    assert report["chosen_iterations"] == report["configured_iterations"] == NEWTON_ITERATIONS == 1
    assert candidates[1]["categories"]["representative"]["max_ulp"] <= 1
    assert candidates[1]["categories"]["adversarial"]["max_ulp"] <= 2
    assert candidates[2]["categories"]["representative"]["max_ulp"] <= 1
    assert candidates[2]["categories"]["adversarial"]["max_ulp"] <= 2
    assert abs(candidates[1]["rsqrt_relative_error"]["mean"]) < 1.0e-5
    assert abs(candidates[1]["output_signed_ulp_mean"]) < 1.0e-3


def test_cycle_and_operation_metadata_is_exact() -> None:
    one = operation_metadata(16, iterations=1)
    two = operation_metadata(16, iterations=2)

    assert one.beats_per_row == 256
    assert one.input_accept_cycles == 256
    assert one.accumulation_replay_cycles == 256
    assert one.finalize_cycles == 5
    assert one.output_issue_cycles == 256
    assert one.output_pipeline_latency == 3
    assert one.no_stall_row_cycles == 776
    assert one.seed_rom_reads == 1
    assert one.newton_multiplications == 3
    assert one.output_multiplications == 8192
    assert one.fixed_point_rne_boundaries == 4
    assert one.bf16_narrow_boundaries == 4096
    assert two.finalize_cycles == 8
    assert two.no_stall_row_cycles == 779
    assert two.newton_multiplications == 6
    assert two.fixed_point_rne_boundaries == 7


def test_exact_output_narrowing_covers_ties_subnormals_and_saturation() -> None:
    assert _round_exact_to_bf16(0, 257, -8) == 0x3F80
    assert _round_exact_to_bf16(0, 259, -8) == 0x3F82
    assert _round_exact_to_bf16(1, 0, 0) == 0x8000
    assert _round_exact_to_bf16(0, 1, -134) == 0x0000
    assert _round_exact_to_bf16(0, 3, -134) == 0x0002
    assert _round_exact_to_bf16(0, 511, 119) == 0x7F80


@pytest.mark.parametrize("iterations", [0, 3])
def test_iteration_count_fails_closed(iterations: int) -> None:
    with pytest.raises(ValueError):
        rmsnorm_bf16_phase2(
            [0x3F80] * HIDDEN_SIZE,
            [0x3F80] * HIDDEN_SIZE,
            lanes=16,
            iterations=iterations,
        )
