# Quality Gate

The evaluator must run `npu/eval/materialize_hf_decoder_contract.py` before
generating reference or candidate manifests. The materializer must produce:

- `runs/datasets/llm_decoder_eval_distilgpt2_prompt_stress_v1/manifest.json`
- `runs/models/llm_decoder_distilgpt2_trained_v1/model_contract.json`
- `runs/tokenizers/llm_decoder_distilgpt2_trained_v1/manifest.json`

The evaluator must then generate fresh reference and candidate manifests,
validate the decoder contract, compare exact reference versus the default
candidate, run `decoder_bf16_pwl_scale_probe_v1`, and summarize the bf16/PWL
baseline and logit tie-break recovery.

The final summary must report baseline misses, recovered sample ids, regression
sample ids, and exact-safe status. Generated ONNX and tokenizer files must
remain uncommitted. The sweep must retain per-sample miss lists so downstream
analysis can group failures by prompt category, entropy, and logit-margin
regime.
