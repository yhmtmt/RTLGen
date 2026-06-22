# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1`
- `title`: `Llama7B measured compute closure with dense GEMM V3 metrics`

## Why This Gate Is Required
PR #981 introduced a corrected measured-compute closure for Llama7B but the compute anchor
was not yet reranked against merged V3 dense-GEMM metrics. The rerank determines whether
the selected family remains feasible under measured `macs_per_cycle` density rather than the 524288 abstract target.

## Reference
- baseline_ref: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_measured_compute_energy_closure__l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json`
- reference_ref: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_command_calibrated_service__l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json`

## Checks
- metric: compare frontier family
  - threshold: PR #981 corrected frontier family must be explicitly represented and the reranked PR #981-v3 family must be logged for decision.
- metric: measured compute source
  - threshold: selected rerank rows must identify the merged V3 dense-GEMM source rows and report required compute replicas/compute area per die.
- metric: source-backed consistency
  - threshold: HBM command-calibrated service and SRAM profile terms remain present in the reranked evidence.

## Local Commands
- command: `python3 npu/eval/audit_llm_decoder_attention_measured_compute_energy_closure.py --hbm-command-calibrated-service-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_command_calibrated_service__l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json --measured-compute-json <merged-l1-v3-dense-compute-artifact.json> --sram-profile-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json --out /tmp/decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1.json --out-md /tmp/decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1.md`

## Result
- status: blocked_until_l1_v3_merged
- note: Blocked until the V3 dense-GEMM source rows are merged and materialized in the remote evaluator queue.
