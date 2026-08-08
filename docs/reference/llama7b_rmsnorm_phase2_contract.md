# Llama-7B BF16 RMSNorm Phase 2 Contract

This document freezes reciprocal-square-root finalization and BF16 output
scaling on top of the Phase 1 48-bit block-floating sum-of-squares contract in
`docs/reference/llama7b_rmsnorm_bf16_contract.md`.

The executable contract is `npu/eval/llama7b_rmsnorm_phase2.py`. The checked
seed ROM is `npu/eval/data/llama7b_rmsnorm_rsqrt_seed_q20.hex`; its sole source
is `npu/eval/generate_llama7b_rmsnorm_rsqrt_seed_rom.py`.

## Frozen configuration

| item | contract |
|---|---|
| hidden size | 4096 |
| epsilon | `1099512 * 2^-40` |
| normalized variance | unsigned `Q2.24`, 26 bits |
| normalized variance interval | `[1, 4)` |
| normalized exponent | even signed integer |
| seed ROM | 192 entries x 21 bits |
| seed and Newton estimate | unsigned `Q1.20`, 21 bits |
| seed address | 8 source bits, raw addresses 64..255 mapped to 0..191 |
| Newton iterations | 1 |
| one-iteration bias correction | exact `+4` in `Q1.20` |
| output products | full-precision unsigned integer |
| output narrowing | BF16 RNE with gradual underflow and infinity saturation |

All right-shift boundaries below use round-to-nearest, ties-to-even (RNE).
Left shifts and explicitly full-precision products are exact.

## Variance and epsilon

Phase 1 supplies:

```text
sum_squares = accumulator_mantissa_48 * 2^accumulator_lsb_exponent
mean_square = accumulator_mantissa_48 * 2^(accumulator_lsb_exponent - 12)
epsilon     = 1099512 * 2^-40
variance    = mean_square + epsilon
```

The epsilon integer is decimal `1e-6` rounded once to the nearest `2^-40`, RNE.
Its represented value is approximately `1.0000003385357559e-6`. No runtime
floating-point epsilon conversion is permitted.

The two nonnegative power-of-two terms are added exactly for specification
purposes. Hardware may use exponent comparison, alignment, guard, round, and
sticky bits, but must produce the same final `Q2.24` result as one RNE operation
on the exact sum. Independent per-term rounding is not equivalent.

Let `h=floor(log2(variance))`. Select the even exponent:

```text
variance_exponent_even = h        when h is even
variance_exponent_even = h - 1    when h is odd
variance_mantissa      = variance * 2^-variance_exponent_even
```

Round `variance_mantissa` once to unsigned `Q2.24`. If rounding produces exactly
`4.0`, replace it with `1.0` and add two to the even exponent. The final
mantissa is in `[1,4)`. For finite input rows, the even exponent is in
`[-20,254]` and fits a signed 9-bit field. The derived rsqrt exponent is in
`[-127,10]` and fits a signed 8-bit field. This normalization is one fixed-point
RNE boundary.

## Seed ROM

For `Q2.24` mantissa integer `M`, form:

```text
raw_address = M >> 18
rom_address = raw_address - 64
```

`raw_address` is in `64..255`; `rom_address` is in `0..191`. Entry `a` uses the
midpoint of its `1/64`-wide mantissa interval:

```text
m_mid = (a + 64 + 0.5) / 64
seed[a] = RNE(2^20 / sqrt(m_mid))
```

Generation uses Python `Decimal` with 80 decimal digits and
`ROUND_HALF_EVEN`. Each checked word is six lowercase hexadecimal digits. The
ROM is monotonically nonincreasing and every seed is strictly between zero and
`1.0` in `Q1.20`.

The guard command is:

```sh
python -m npu.eval.generate_llama7b_rmsnorm_rsqrt_seed_rom --check
```

Any missing byte, extra line, case change, width change, or value mismatch fails
the guard. The ROM must be regenerated, never hand-edited.

## Newton iteration

The frozen update is `y <- y * (1.5 - 0.5*m*y*y)`. One iteration has exactly
three multiplier stages and three RNE boundaries:

1. `y_square_q20 = RNE((y_q20 * y_q20) / 2^20)`.
   The `21x21` product is kept at 42 bits; the result is unsigned `Q1.20`.
2. `half_m_y_square_q20 = RNE((m_q24 * y_square_q20) / 2^25)`.
   The `26x21` product is kept at 47 bits; the result is unsigned `Q2.20`.
   Form `correction_q20 = 1.5_q20 - half_m_y_square_q20` exactly in `Q2.20`.
3. `updated_q20 = RNE((y_q20 * correction_q20) / 2^20) + 4`.
   The `21x22` product is kept at 43 bits. Saturate only this result to unsigned
   21-bit `Q1.20`; the addition is exact and folded before saturation. The
   proven legal range does not invoke saturation.

The scaled reciprocal square root is:

```text
rsqrt = updated_q20 * 2^-20 * 2^rsqrt_exponent
rsqrt_exponent = -(variance_exponent_even / 2)
```

The exact `+4` correction applies only to the selected one-iteration candidate.
It removes the small systematic low bias of a midpoint-seeded Newton step
without another multiplier or cycle. The evaluated two-iteration candidate
repeats all three uncorrected stages with the first result as the next input.
There is no hidden truncation, fused operation, or reassociation.

## Output multiplication and BF16 narrowing

Decode each finite BF16 row/gamma word as an unsigned at-most-8-bit significand
and signed binary exponent, preserving its sign separately. Per element:

```text
coefficient = row_significand * updated_q20 * gamma_significand
exponent = row_exponent + gamma_exponent + rsqrt_exponent - 20
sign = row_sign XOR gamma_sign
```

The first `8x21` product and subsequent at-most-29x8 product retain every bit;
there is no intermediate rounding or saturation. The final coefficient is at
most 37 bits.

Narrow `coefficient * 2^exponent` once:

- For a normal result, retain the leading eight significand bits and RNE all
  discarded bits. Renormalize a rounding carry. Saturate exponent overflow to
  signed infinity.
- For a subnormal result, align directly to BF16 unit `2^-133` and RNE once.
  A carry into 128 becomes the minimum normal.
- An exact zero retains `sign(row) XOR sign(gamma)`.
- Gradual underflow is required. Finite arithmetic cannot create NaN.

Input exponent 255 retains the Phase 1 canonical protocol behavior: all output
words are `0x7fc0`, `protocol_error` is asserted, and exposed arithmetic state is
zero. Maximum-finite, finite subnormal, and signed-zero inputs are valid data.

## Candidate selection

`npu/eval/evaluate_llama7b_rmsnorm_phase2.py` evaluates both iteration counts
against an independently decoded, max-scaled FP64 oracle. The deterministic
suite contains 28 representative Llama-like/random rows and 29 adversarial
finite rows, for 233472 output comparisons per candidate.

| iterations | representative exact | representative max ULP | adversarial exact | adversarial max ULP | mean rsqrt relative error | max abs rsqrt relative error |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 99.898856% | 1 | 99.962958% | 1 | -1.464781e-7 | 1.952717e-5 |
| 2 | 99.981689% | 1 | 100.000000% | 0 | 2.359628e-7 | 1.956298e-6 |

Both candidates meet the required limits of at most one BF16 ULP on
representative rows and at most two BF16 ULP on adversarial rows. One iteration
is selected because it removes three finalize cycles and three fixed-point
multiplications per row. Its exact final `+4` correction centers mean rsqrt scale
error at `-1.46e-7` and mean signed output error at `-8.566338e-6` ULP, below the frozen bias gates of
`1e-5` relative rsqrt error and `1e-3` signed output ULP.

The exact generated measurements are checked in at
`docs/reference/llama7b_rmsnorm_phase2_evaluation.json`.

## Cycle and operation contract

Let `B=4096/LANES`. No phases overlap. Under continuous ready/valid service:

| phase | cycles | operation |
|---|---:|---|
| `ACCEPT_MAX` | B | accept/store row and gamma, classify, select Phase 1 maximum |
| `ACCUMULATE_REPLAY` | B | Phase 1 exact square alignment and 48-bit integer sum |
| `F0_NORMALIZE` | 1 | exact mean/epsilon alignment, leading exponent, Q2.24 RNE |
| `F1_SEED` | 1 | registered seed ROM read |
| `F2_Y_SQUARE` | 1 | Newton multiplier/RNE stage 1 |
| `F3_M_Y_SQUARE` | 1 | Newton multiplier/RNE stage 2 and exact correction subtract |
| `F4_UPDATE` | 1 | Newton multiplier/RNE/saturation stage 3 |
| `OUTPUT_ISSUE` | B | issue one `LANES`-wide stored row/gamma beat per cycle |
| output drain | 3 | exact product stage 1, exact product stage 2, BF16 narrowing |

The no-stall row latency from first accepted input beat through accepted final
output beat is `3*B + 8` cycles. At 16 lanes, `B=256` and latency is 776 cycles.
The output pipeline has latency 3 and initiation interval 1. Backpressure holds
all output data and metadata stable and extends latency by the exact stall count.

Per valid row, the frozen operation counts are:

- one seed ROM read
- three Newton multiplications and three Newton RNE boundaries
- one variance-normalization RNE boundary
- 8192 exact output multiplications
- 4096 BF16 RNE/saturation boundaries

A two-iteration evaluation uses six Newton multiplications, seven total
fixed-point RNE boundaries, eight finalize cycles, and `3*B + 11` no-stall row
cycles. Protocol-error rows reserve the same phase/cycle schedule and emit the
canonical row; arithmetic resources may be clock-gated without changing timing.

This contract freezes arithmetic and cycle semantics only. No RTL is introduced
in Phase 2.
