# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_topology_derived_schedule_llama7b_v1`
- `title`: `Llama7B dense tile topology-derived scheduler frontier`

## Why This Gate Is Required
- The previous topology-pair result showed the abstract 65kB/cycle one-hop NoC target is not a proven topology.
- The scheduler frontier must be recomputed using coupled topology service rows before it guides NoC/SRAM design.

## Reference
- topology_pairs_ref: `l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2`
- implementation_min_commit: `650081546b870d025144cc530425e9847d4d30f0`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: topology service rows
  - threshold: output must cite the number of topology service rows used
- metric: abstract NoC knobs
  - threshold: generated task command must not include independent `--noc-bandwidth-bytes-per-cycle` or `--noc-hops`
- metric: frontier comparison
  - threshold: report must include best topology/scheduler and gap to the previous abstract NoC service target

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_topology_derived_schedule.py --repo-root . --topology-pairs-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_dense_tile_topology_scheduler_pairs__l2_decoder_attention_kv_dense_tile_topology_scheduler_pairs_llama7b_v1_r2.json --out /tmp/topology_derived.json --out-md /tmp/topology_derived.md`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
