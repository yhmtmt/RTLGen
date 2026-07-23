# Evaluation Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
- `item_id`: `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`

## Required Inputs
- merged/materialized dependency:
  - `l2_decoder_attention_decode_score_multivalue_cluster_equivalence_llama7b_v1`
- proposal implementation merged onto `origin/master`

## Expected Outputs
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_decode_score_multivalue_integrated_service__l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1.md`

## Dispatch Contract
- abstraction layer:
  - `decoder_attention_decode_score_multivalue_integrated_service`
- task type:
  - `l2_campaign`
- expected direction:
  - `record_decode_score_multivalue_integrated_service_probe`

## Gate Condition
- The run must remain evidence-only and must not claim NoC/HBM/physical/token-energy closure.
