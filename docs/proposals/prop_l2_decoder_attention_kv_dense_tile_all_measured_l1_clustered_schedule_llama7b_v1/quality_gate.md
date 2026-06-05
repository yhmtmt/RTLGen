# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_all_measured_l1_clustered_schedule_llama7b_v1`
- `title`: `Llama7B dense tile all-measured clustered schedule`

## Why This Gate Is Required
- The current Llama7B frontier may move when measured dense tile PPA replaces the older compute block source inside the clustered schedule model.
- The result must preserve explicit residuals for analytic SRAM service and global NoC arbitration.

## Reference
- dense_compute_ref: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- measured_l1_ref: `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: selected compute source
  - threshold: selected rows must cite `compute_source=dense_gemm_tile`
- metric: measured L1 profile
  - threshold: output must charge a non-analytic measured L1 profile

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_clustered_schedule.py --compute-source dense_gemm_tile --tag-substring npu_dense_gemm_tile_v2_scale_hier ...`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
