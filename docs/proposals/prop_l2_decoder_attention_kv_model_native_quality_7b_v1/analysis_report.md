# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- `candidate_id`: `l2_decoder_attention_kv_model_native_quality_7b_v1`

## Evaluations Consumed
- pending work item: `l2_decoder_attention_kv_model_native_quality_7b_v1`
- source commit at initial staging: `78bf63f25a05b7798ee98e4607d4882f7a2ce468`
- expected output:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality_7b__l2_decoder_attention_kv_model_native_quality_7b_v1.json`

## Baseline Comparison
- TinyLlama native quality accepted KV8 but rejected KV4 tensor quantization.
- TinyLlama native recovery still rejected KV4 after `kv_head` and
  `token_vector` scale granularity.
- This run checks whether the same conclusion holds at a larger checkpoint
  scale before the Llama7B frontier treats KV4 as promotable.

## Result
- status: pending remote evaluator result
- decision rule:
  - KV8 pass reinforces the conservative quality-backed frontier.
  - KV4 pass opens a follow-up hardware metadata/QAT evaluation path.
  - KV4 fail keeps KV4 as an unpromoted hardware-benefit experiment.

## Failures and Caveats
- Default model is a 7B-class native-GQA checkpoint, not exact Llama7B/GQA8.
- Exact LLaMA-family runs may require evaluator-local credentials.
- Teacher-forced prompts are a gate only; full perplexity and task accuracy
  remain future work.

## Recommendation
- Wait for remote result.
- Do not promote KV4 in the main Llama7B architecture ranking until this or a
  stronger real-checkpoint quality gate passes.
