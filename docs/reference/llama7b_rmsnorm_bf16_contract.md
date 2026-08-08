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

Phase 1 provides a contract, executable model, and tests only. It does not
provide RTL, PPA evidence, or an approximation for reciprocal square root.

## Software input contract

- `row` and `gamma` each contain exactly `4096` raw unsigned BF16 words.
- Every word is an integer in `[0x0000, 0xffff]`; Python `bool` is not accepted.
- `lanes` is a positive integer divisor of `4096`.
- Shape, lane, and word validation completes before arithmetic starts. A
  malformed argument raises `ValueError` and returns no partial output.
- A legal lane count changes only the streaming grouping. It cannot change the
  numerical result.

## BF16 classification

BF16 uses one sign bit, eight exponent bits, and seven fraction bits.

- Exponent `0`: signed zero when the fraction is zero, otherwise a subnormal.
  Both are accepted and decoded exactly as FP32 values by appending 16 zero
  fraction bits. No flush-to-zero mode is used.
- Exponents `1..254`: accepted finite normal values.
- Exponent `255`: infinity or NaN, regardless of sign or payload. Any such word
  in either `row` or `gamma` makes the whole transaction a protocol error.

On an exponent-255 input, the canonical result is `protocol_error=True`, all
`4096` output words equal to canonical quiet NaN `0x7fc0`, and all exposed
arithmetic-state fields equal to zero. No input NaN payload or sign propagates,
and no valid prefix is emitted. This behavior is data-independent after input
validation.

## Internal arithmetic

Inputs are exact BF16 values embedded in IEEE-754 binary32. Internal operations
use binary32 round-to-nearest, ties-to-even (RNE), with gradual underflow:

1. Traverse logical indices `0..4095`. For each index, round `x[i] * x[i]` to
   FP32, then round `sum_squares + square` to FP32. The initial sum is `+0`.
2. Multiply the completed sum by exact binary `2^-12` (`0x39800000`) and round
   to FP32.
3. Add epsilon. Decimal `1e-6` is represented by FP32 word `0x358637bd`; round
   the addition to FP32.
4. Square root, then `1.0 / root`, are each rounded to FP32 RNE.
5. For each output, round `x[i] * inv_rms` to FP32, then round that result times
   `gamma[i]` to FP32.
6. Narrow FP32 to BF16 RNE once, preserving sign. A halfway value increments
   only when the retained BF16 least-significant bit is one.

The reference uses an ascending-index scalar accumulation even when `lanes > 1`.
An RTL implementation must fold accepted lanes in lane-number order into the
same scalar state, or prove bit equivalence to that order. Reassociation,
fused multiply-add, wider accumulation, reciprocal-square-root approximation,
and intermediate BF16 rounding do not conform to this Phase 1 model.

Finite arithmetic overflow follows IEEE-754. It can produce infinity in exposed
internal state or output without setting the input protocol-error flag. This is
distinct from receiving an exponent-255 input.

## Zero and subnormal behavior

- Input subnormals participate without flushing. Their square may round to
  FP32 zero according to FP32 RNE.
- Epsilon keeps the reciprocal-square-root operand positive for an all-zero or
  underflowed row.
- FP32 and BF16 signed zeros are preserved. Since `inv_rms` is nonnegative, an
  exact-zero output has sign `sign(x) XOR sign(gamma)` under IEEE multiplication.
- BF16 output underflow is gradual and rounds to a signed zero only when required
  by BF16 RNE.

## Eventual streaming state contract

The eventual RTL transaction has `4096 / LANES` accepted input beats and the
same number of output beats. Beat `b`, lane `l` maps only to logical index
`b * LANES + l`; lanes are contiguous and ascending.

The required conceptual phases are:

1. `IDLE/ACCEPT`: accept paired row and gamma lanes, classify every word, store
   both vectors for replay, and update one FP32 `sum_squares` state in lane order.
2. `FINALIZE`: after exactly 4096 accepted elements, compute mean square,
   epsilon addition, square root, and reciprocal with the boundaries above.
3. `EMIT`: replay stored row/gamma in original order and emit each BF16 result.
4. `ERROR_EMIT`: if any accepted input had exponent 255, emit only canonical
   `0x7fc0` words and assert the transaction protocol-error status.

State advances only on ready/valid handshakes. Input data and framing must stay
stable while stalled; output data, index, last, and error status must stay stable
while stalled. `last` is true only on the final input/output beat. Early or
missing input `last`, an unpaired row/gamma beat, a beat outside an active row,
or accepting more than `4096` elements is a framing protocol error. Reset or a
fully accepted final output beat clears row-local arithmetic, index, and sticky
error state before another row can be accepted.

No normal output may be exposed before classification of the complete input row,
which ensures a late exponent-255 input still canonicalizes the entire output.
