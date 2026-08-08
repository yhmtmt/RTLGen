# Llama-7B BF16 RMSNorm Contract

This document defines the Phase 1 numerical and eventual streaming contract for
a Llama-7B transformer RMSNorm block. The executable reference is
`npu/eval/llama7b_rmsnorm_reference.py`.

## Scope

The operation is transformer RMSNorm over one hidden row:

```text
mean_square = sum(x[i] * x[i], i=0..4095) / 4096
inv_rms     = 1 / sqrt(mean_square + 1e-6)
y[i]        = (x[i] * inv_rms) * gamma[i]
```

There is no mean subtraction and no softmax, exponential, row-sum reciprocal,
or probability normalization. Hidden size is fixed at `4096`; epsilon is fixed
at decimal `1e-6`.

Phase 1 freezes a bit-exact block-floating sum-of-squares contract. Reciprocal
square root, output multiplication, and output rounding remain provisional
software semantics. Phase 1 does not provide RTL, PPA evidence, or a bit-exact
claim for the complete RMSNorm operation.

## Software input contract

- `row` and `gamma` each contain exactly `4096` raw unsigned BF16 words.
- Every word is an integer in `[0x0000, 0xffff]`; Python `bool` is not accepted.
- `lanes` is a positive integer divisor of `4096`.
- Shape, lane, and word validation completes before arithmetic starts. A
  malformed argument raises `ValueError` and returns no partial output.
- A legal lane count changes only streaming grouping. It cannot change
  accumulation state or provisional output.

## BF16 classification

BF16 uses one sign bit, eight exponent bits, and seven fraction bits.

- Exponent `0`: signed zero when the fraction is zero, otherwise a subnormal.
  Both are accepted without flush-to-zero.
- Exponents `1..254`: accepted finite normal values.
- Exponent `255`: infinity or NaN, regardless of sign or payload. Any such word
  in either `row` or `gamma` makes the whole transaction a protocol error.

On an exponent-255 input, the canonical result is `protocol_error=True`, all
`4096` output words equal to canonical quiet NaN `0x7fc0`, integer accumulation
state equal to zero, and provisional inverse RMS equal to `0.0`. No input NaN
payload or sign propagates, and no valid prefix is emitted.

## Exact BF16 square decomposition

Each finite BF16 magnitude is represented as an unsigned integer significand
times a power of two:

```text
exponent field E = 0:       x = fraction       * 2^-133
exponent field E = 1..254:  x = (128+fraction) * 2^(E-134)
```

The sign is irrelevant to the square. Each square is formed exactly as
`coefficient * 2^term_exponent`, where `coefficient` is the at-most-16-bit
integer significand square and `term_exponent` is twice the value exponent.

## Bit-exact 48-bit accumulation

The row uses a shared block-floating scale selected before accumulation:

1. For every nonzero exact square, compute
   `square_exponent = floor(log2(coefficient)) + term_exponent`.
2. Let `max_square_exponent` be the maximum of those values.
3. Set `accumulator_lsb_exponent = max_square_exponent - 34`.
4. Align every exact square to that LSB exponent. Right shifts use unsigned
   round-to-nearest, ties-to-even. Left shifts are exact.
5. Sum the aligned nonnegative integers without reassociation-dependent
   rounding into `accumulator_mantissa_48`.

An all-zero row has mantissa, LSB exponent, and maximum square exponent all zero.
For a nonzero finite row, `max_square_exponent` is in `[-266, 255]` and
`accumulator_lsb_exponent` is in `[-300, 221]`; each therefore fits a signed
10-bit field. The represented sum is:

```text
sum_squares_bfp = accumulator_mantissa_48 * 2^accumulator_lsb_exponent
```

The largest aligned term has its leading one at bit 34 and is less than `2^35`
before alignment rounding. RNE can produce at most `2^35` per term. With exactly
`4096 = 2^12` terms, the conservative sum bound is `2^47`, which fits an unsigned
48-bit accumulator. Therefore every combination of 4096 finite BF16 inputs is
covered without accumulator overflow. This bound is independent of input order
and lane count.

The alignment quantization window retains 34 bits below the largest square's
leading bit. A term below half of the shared LSB rounds to zero. This bounded
loss is intentional Phase 1 behavior and is checked against a separate robust
scaled FP64 oracle.

## Provisional finalization

The following behavior produces useful quality vectors but is not a bit-exact
RTL contract:

1. Convert the block-floating sum exactly to binary64 and divide by 4096 with a
   power-of-two exponent adjustment.
2. Compute `1 / sqrt(mean_square + 1e-6)` with the host binary64 square root and
   division operations.
3. Multiply each exact BF16 input by that inverse RMS and its exact BF16 gamma in
   binary64.
4. Round binary64 directly to BF16 with round-to-nearest, ties-to-even, preserving
   signed zero and gradual BF16 underflow.

These operations are correctly scaled for the full finite BF16 input range: an
all-maximum-finite row with `gamma=1` produces approximately `+1` (`0x3f80`), not
zero, and does not set `protocol_error`.

Phase 2 must select the reciprocal-square-root implementation, including LUT
addressing and contents, seed precision, Newton iteration count, intermediate
widths, normalization shifts, and rounding/saturation after every operation.
It must also freeze output multiply and BF16 narrowing boundaries. Only then may
the complete RMSNorm path claim bit-exact RTL equivalence. The Phase 1
`provisional_inv_rms` field is diagnostic and must not be used as an RTL golden
bit pattern.

## Zero and subnormal behavior

- Input subnormals participate in exact square decomposition without flushing.
  Their aligned square may round to zero under the documented block scale.
- Epsilon keeps the provisional reciprocal-square-root operand positive for an
  all-zero or quantized-zero sum.
- Signed-zero inputs and gamma values are preserved. Since provisional
  `inv_rms` is positive, an exact-zero output has sign
  `sign(x) XOR sign(gamma)`.
- Provisional BF16 output underflow is gradual and rounds to signed zero only
  when required by BF16 RNE.

## Exposed result fields

- `output`: 4096 provisional BF16 words.
- `protocol_error`: canonical row-level input classification error.
- `accumulator_mantissa_48`: bit-exact unsigned 48-bit accumulation mantissa.
- `accumulator_lsb_exponent`: signed power-of-two weight of accumulator bit 0.
- `max_square_exponent`: selected row maximum used to derive the block scale.
- `provisional_inv_rms`: binary64 software value, diagnostic only.

## Eventual streaming state contract

The eventual RTL transaction has `4096 / LANES` accepted input beats and the
same number of output beats. Beat `b`, lane `l` maps only to logical index
`b * LANES + l`; lanes are contiguous and ascending.

The required conceptual phases are:

1. `IDLE/ACCEPT_MAX`: accept paired row and gamma lanes, classify every word,
   store both vectors, and determine `max_square_exponent` over the complete row.
2. `ACCUMULATE_REPLAY`: replay stored row values, align exact squares to the
   selected shared exponent, and update the 48-bit integer sum. Lane-local terms
   are integer-added; no intermediate narrowing or order-dependent rounding is
   allowed.
3. `FINALIZE`: apply the Phase-2-frozen mean, epsilon, reciprocal-square-root,
   and output-scale contract. Until Phase 2, software uses provisional semantics.
4. `EMIT`: replay stored row/gamma in original order and emit BF16 results.
5. `ERROR_EMIT`: if any accepted input had exponent 255, emit only canonical
   `0x7fc0` words and assert transaction protocol-error status.

State advances only on ready/valid handshakes. Input data and framing must stay
stable while stalled; output data, index, last, and error status must stay stable
while stalled. `last` is true only on the final input/output beat. Early or
missing input `last`, an unpaired row/gamma beat, a beat outside an active row,
or accepting more than `4096` elements is a framing protocol error. Reset or a
fully accepted final output beat clears row-local state before another row can
be accepted.

No normal output may be exposed before classification of the complete input row,
which ensures a late exponent-255 input canonicalizes the entire output.
