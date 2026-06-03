# Implementation Summary

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- `title`: `Llama7B physical HBM compute sensitivity`

## Scope
- Materialized a Layer 2 campaign that sweeps compute throughput for Llama7B
  131k native-GQA KV8 decode attention under the physical HBM/SRAM/NoC planning
  model.
- Reused the merged all-measured local L1 clustered baseline as the paired
  input.
- Did not add RTL, mapper logic, new approximation formats, or full routed NoC
  modeling.

## Files Changed
- `docs/proposals/prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2/*`
- `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse/campaign__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json`
- `runs/campaigns/npu/e2e_eval_mlp_smoke_v1_reuse__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2/*`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.md`

## Local Validation
- The remote evaluator reported `6/6` commands succeeded for
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`.
- Submission uses the merged control-plane materializer that writes inline
  artifacts even when stored inline hashes drift from recomputed file hashes.

## Evaluation Request
- requested remote task:
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- cost class: `medium`
- baseline:
  `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`

## Risks
- The decisive memory and NoC quantities remain planning-model estimates.
- Compute throughput values are not yet backed by concrete clustered RTL/PPA at
  the largest settings.
- The result should guide the next measured design points rather than be treated
  as a final chip architecture.
