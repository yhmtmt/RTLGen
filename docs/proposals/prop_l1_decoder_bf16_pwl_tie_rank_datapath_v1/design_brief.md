# Design Brief

## Problem

The decoder bf16/PWL recovery run showed that the two exact-next misses were
recovered by using logits only as an exact score tie-break key. The current
frontier cost model still lacks a measured hardware cost for that rank step.

## Hypothesis

An 8-lane unsigned 16-bit score ranker with a signed 16-bit logit tie-break
comparator is small enough that bf16/PWL remains the likely low-cost frontier,
but it should be priced by OpenROAD before being folded into the ranking view.

## Evaluation Scope

- Generate and synthesize `score_tie_rank_r8_s16_l16`.
- Record Nangate45 area, timing, and power from the standard high-utilization
  Layer 1 sweep.
- Do not rerun decoder quality; this proposal only prices the recovery datapath.

## Follow-On

If the isolated ranker cost is material, measure an integrated decoder output
rank block and compare against a q12 fallback path.
