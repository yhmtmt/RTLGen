# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- `title`: `Llama7B physical HBM compute sensitivity`

## Why This Gate Is Required
This pass changes the architectural interpretation of the Llama7B 131k
frontier by varying effective compute throughput. It must not silently change
model quality assumptions or compare native GQA8 KV8 against approximation
formats.

## Reference
- baseline_ref:
  `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`
- reference_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_physical_hbm_compute_sensitivity__l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2.json`

## Checks
- metric: model and sequence identity
  - threshold: Llama7B proxy, sequence length 131072, hidden size 4096, 32
    layers, native GQA8 KV8 only.
- metric: resource-boundary visibility
  - threshold: report must retain MAC/cycle, vector-op/cycle, die area,
    HBM share, latency, and dominant resource for each boundary point.

## Local Commands
- command:
  `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed
- note: The generated dataset artifact preserves native GQA8 KV8 assumptions
  and reports resource labels for the compute sweep.
