# Evaluation Gate

Queue `l2_decoder_pwl_survivor_distribution_v1` only after
`l2_decoder_pwl_logit_ladder_v1` is merged and finalized.

Required merged inputs:

- `runs/datasets/llm_decoder_eval_tiny_v1/decoder_pwl_logit_ladder__l2_decoder_pwl_logit_ladder_v1.json`
- `runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json`
- `npu/eval/summarize_llm_decoder_pwl_survivor_distribution.py`
