# Evaluation Gate

Queue `l2_decoder_bf16_pwl_recoverability_v1` after the broad q8/bf16
distribution result and the PWL bit-width boundary result are merged.

Required inputs:

- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_norm_distribution_broad_v2.json`
- `runs/datasets/llm_decoder_eval_tiny_v1/samples_distribution_v2.jsonl`
- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_pwl_bitwidth_boundary__l2_decoder_pwl_bitwidth_boundary_v1.json`
