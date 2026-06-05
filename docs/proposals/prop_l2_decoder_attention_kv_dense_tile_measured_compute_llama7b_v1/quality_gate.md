# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- `title`: `Llama7B dense tile measured compute substitution`

## Why This Gate Is Required
- The Llama7B 131k frontier may move when measured dense tile PPA replaces the older compute block source.

## Reference
- baseline_ref: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- reference_ref: `l1_npu_dense_gemm_tile_scaling_v2`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: selected compute source
  - threshold: all selected rows must cite dense GEMM tile metrics

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_measured_compute.py --compute-source dense_gemm_tile ...`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
