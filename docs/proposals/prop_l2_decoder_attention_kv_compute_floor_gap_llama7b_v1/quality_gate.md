# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- `title`: `Llama7B attention/KV compute floor gap`

## Why This Gate Is Required
The result changes the next-step priority between compute architecture and
memory/NoC modeling. It must preserve the same Llama7B 131k native-GQA KV8
assumptions used by the compute-sensitivity result.

## Reference
- baseline_ref:
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- reference_ref:
  `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_compute_floor_gap__l2_decoder_attention_kv_compute_floor_gap_llama7b_v1.json`

## Checks
- metric: source floor
  - threshold: use the merged physical-HBM compute-sensitivity artifact from
    PR #750.
- metric: measured compute source
  - threshold: use merged measured-compute and measured-compute-partition
    artifacts only.
- metric: output fields
  - threshold: report gap by die, best measured density, and required compute
    area fraction.

## Local Commands
- command:
  `python3 scripts/validate_runs.py --skip_eval_queue`

## Result
- status: passed
- note: The output reports all required gap quantities and does not change
  quality or KV-sharing assumptions.
