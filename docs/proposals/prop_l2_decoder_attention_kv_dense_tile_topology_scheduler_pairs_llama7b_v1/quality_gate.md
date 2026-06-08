# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1`
- `title`: `Llama7B dense tile topology/scheduler pairs`

## Why This Gate Is Required
- The previous frontier used independent NoC bandwidth, hop, cluster-count, and reduction knobs.
- The next architecture ranking should only consume topology/scheduler pairs that can coexist logically.
- The report must make invalid combinations explicit so future scheduler jobs can filter them.

## Reference
- reduction_noc_frontier: `l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1`
- implementation_min_commit: `c93db2ccf9c8e92a2d1fe6a1ac5a85dc5e61181c`

## Checks
- metric: valid pair count
  - threshold: nonzero successful output
- metric: invalid pair count
  - threshold: nonzero rejected output with explicit invalid reasons
- metric: previous bandwidth gap
  - threshold: report must compare valid topology service to the previous 65kB/cycle one-hop service target
- metric: next-sweep readiness
  - threshold: output must include `best_valid_pairs`

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_topology_scheduler_pairs.py --repo-root . --frontier-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dense_tile_reduction_noc_frontier__l2_decoder_attention_kv_dense_tile_reduction_noc_frontier_llama7b_v1.json --out /tmp/topology_pairs.json --out-md /tmp/topology_pairs.md`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
