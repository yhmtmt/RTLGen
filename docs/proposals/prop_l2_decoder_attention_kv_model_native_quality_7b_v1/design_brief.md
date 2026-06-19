# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_model_native_quality_7b_v1`
- `title`: `Evaluate 7B-class native KV quantization quality`

## Problem
- The current Llama7B architecture frontier still uses synthetic/proxy evidence
  for the precision risk of low-bit KV cache.
- TinyLlama native-GQA evidence accepts KV8 but rejects KV4, even after
  scale-granularity recovery. We need a larger trained checkpoint before
  deciding whether KV4 remains only a hardware-benefit experiment.

## Hypothesis
- A 7B-class native checkpoint quality run can either reinforce KV8 as the
  conservative deployable point or expose enough KV4 stability to justify a
  follow-up recovery/QAT path.

## Evaluation Scope
- direct comparison set:
  - full-precision cache feedback versus KV8 and KV4 quantized cache feedback
    during teacher-forced decode
  - top-1 match, top-k contains, logit cosine, probability KL, reference margin,
    and max absolute logit delta
- evaluation modes:
  - `frontier_detail`
  - precision gate; not PPA and not broad ranking
- dependency order:
  - requires merged generator support from PR #927
  - requires evaluator-local Hugging Face runtime/model access
- excluded first-stage comparisons:
  - QAT/fine-tuning recovery
  - full perplexity/task-accuracy evaluation
  - OpenROAD/PPA
- follow-on broad sweep:
  - if KV4 passes, price hardware scale metadata and rerun the Llama7B frontier
  - if KV4 fails, keep the quality-backed frontier at KV8 and plan QAT or safer
    quantization formats

## Knowledge Inputs
- TinyLlama native quality:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_quality__l2_decoder_attention_kv_model_native_quality_tinyllama_v1_r2.json`
- TinyLlama native recovery:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_model_native_recovery__l2_decoder_attention_kv_model_native_recovery_tinyllama_v1.json`
- Llama7B quality gate:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_quality_gate__l2_decoder_attention_kv_quality_gate_llama7b_v1.json`

## Candidate Direction
- Add a source-pinned L2 work item using
  `decoder_attention_kv_model_native_quality_7b`.
- Default to `mistralai/Mistral-7B-v0.1` with GQA group size 4, while allowing
  evaluator overrides for exact LLaMA-family checkpoints.

## Direction Gate
- status: approved_for_remote_dispatch
- approved_by: developer_agent
- approved_utc: 2026-06-19T13:54:00Z
- note: remote evaluator only; do not run this model job in the devcontainer.
