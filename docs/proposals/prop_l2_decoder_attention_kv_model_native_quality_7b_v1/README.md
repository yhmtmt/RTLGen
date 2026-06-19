# 7B-Class Native KV Quality Gate

This proposal stages a remote evaluator job for a real-checkpoint KV-cache
quantization quality gate.

The job runs `npu/eval/evaluate_llm_decoder_model_native_kv_quant.py` through
`npu/eval/run_hf_eval_python.sh` and compares teacher-forced decode logits with
KV8 and KV4 quantized `past_key_values`.

Default model settings:

- `RTLGEN_MODEL_NATIVE_7B_MODEL_ID`: defaults to `mistralai/Mistral-7B-v0.1`
- `RTLGEN_MODEL_NATIVE_7B_EXPECTED_GQA_GROUP_SIZE`: defaults to `4`

The evaluator can override those variables for an exact access-controlled
LLaMA-family checkpoint. The work item is remote-only; it must not run on the
devcontainer/local evaluator.
