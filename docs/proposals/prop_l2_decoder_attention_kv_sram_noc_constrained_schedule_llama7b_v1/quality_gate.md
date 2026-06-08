# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1`
- `title`: `Llama7B SRAM/NoC constrained dense tile scheduler frontier`

## Why This Gate Is Required
- The topology-derived schedule still inherited an optimistic SRAM-bank service abstraction.
- The next Llama7B frontier should be interpreted under practical SRAM-bank and endpoint service caps before selecting a detailed NoC/SRAM implementation target.

## Reference
- topology_derived_ref: `l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1`
- sram_profile_ref: `l2_decoder_attention_sram_profile_v1`
- implementation_min_commit: `3a04282a22036915b9ad193ee2351dd2cf19dc64`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: cap-source accounting
  - threshold: report must include practical NoC cap-source counts
- metric: practical SRAM bank service
  - threshold: output must cite SRAM bank port bytes per cycle and local tile-buffer bytes
- metric: abstract NoC knobs
  - threshold: generated task command must not include independent `--noc-bandwidth-bytes-per-cycle` or `--noc-hops`
- metric: frontier comparison
  - threshold: report must include slowdown versus the topology-derived schedule

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_sram_noc_constrained_schedule.py --repo-root . --topology-derived-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dense_tile_topology_derived_schedule__l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1.json --sram-profile-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json --frontier-row-limit 256 --out /tmp/sram_noc_constrained.json --out-md /tmp/sram_noc_constrained.md`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
