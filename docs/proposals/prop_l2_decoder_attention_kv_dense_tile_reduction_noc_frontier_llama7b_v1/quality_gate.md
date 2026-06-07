# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1`
- `title`: `Llama7B dense tile reduction/NoC frontier`

## Why This Gate Is Required
- The previous dense clustered result made cross-tile reduction the dominant resource at the best point.
- The next architecture decision depends on whether SRAM placement, NoC bandwidth/hops, or reduction hierarchy dominates when dense compute is fixed.

## Reference
- dense_clustered_ref: `l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- compute_anchor: `dense_gemm_16x8_k1_p1`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: compute source
  - threshold: selected rows must cite `compute_source=dense_gemm_tile`
- metric: compute architecture
  - threshold: selected rows must cite `dense_gemm_16x8_k1_p1`
- metric: frontier classification
  - threshold: output must retain best-by-memory/NoC and best-by-reduction rows

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py --compute-source dense_gemm_tile --compute-arch-list dense_gemm_16x8_k1_p1 ...`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
