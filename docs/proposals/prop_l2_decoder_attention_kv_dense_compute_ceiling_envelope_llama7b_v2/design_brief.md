# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2`
- `title`: `Llama7B dense compute ceiling envelope V2`

## Problem
The previous compute ceiling envelope used `nm64_flat` as measured RTLGen best
density. The merged dense GEMM tile result now provides a better measured
compute-density point, so the Llama7B frontier should be recalculated before
choosing between dense tile scaling and detailed SRAM/NoC modeling.

## Evaluation Scope
- inputs: merged compute-sensitivity, measured-compute, and design-registry
  records.
- measured density source: best valid internal registry row.
- expected measured best: `rtlgen_npu_dense_gemm_tile_fp16_8x8_k1_p1_nangate45`.
- continuity envelopes: 150 and 300 MAC/cycle/mm2.
- die sizes: 400, 800, and 1200 mm2.
- logic fractions: 0.2, 0.4, and 0.6.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-04T00:00:00Z
- note: This is a low-cost analytic planning gate over merged artifacts.
