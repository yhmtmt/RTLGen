# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- `title`: `Evaluate 7B-class native KV quantization quality`

## Why This Gate Is Required
- KV-cache precision directly changes attention logits and therefore next-token
  rankings. Proxy-only quality is not enough to promote KV4 in the Llama7B
  frontier.

## Reference
- baseline_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality__l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json`
- recovery_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_recovery__l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json`

## Checks
- KV8 top-1 match:
  - threshold: `>= 0.995`
- KV4 promotion:
  - threshold: top-1 `>= 0.98` and top-k contains `>= 0.995`
- model shape:
  - threshold: reported GQA group size must match
    `RTLGEN_MODEL_NATIVE_7B_EXPECTED_GQA_GROUP_SIZE`

## Local Commands
- none; this is a remote evaluator job.

## Result
- status: pending_remote_result
- note: The queued job records the JSON/Markdown evidence used by the next
  precision-frontier decision.
