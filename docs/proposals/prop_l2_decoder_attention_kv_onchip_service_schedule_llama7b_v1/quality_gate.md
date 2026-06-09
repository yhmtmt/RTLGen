# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_onchip_service_schedule_llama7b_v1`
- `title`: `Llama7B on-chip SRAM/NoC service scheduler frontier`

## Why This Gate Is Required
- The SRAM/NoC constrained result still uses a simple min-cap service model.
- We need to know whether arbitration, queue depth, router hop latency, packetization, or schedule policy dominates before choosing an RTL block to embody.
- HBM/DRAM changes are explicitly out of scope for this job.

## Reference
- sram_noc_constrained_ref: `l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2`
- implementation_min_commit: `2a03f9f8ad8bda90315946c41ac2b1e7d1d8bc33`

## Checks
- metric: generated rows
  - threshold: nonzero successful output
- metric: on-chip policy accounting
  - threshold: report must include best rows by schedule/bank policy and queue/router setting
- metric: HBM/DRAM isolation
  - threshold: generated task command must not include HBM/DRAM data-rate or bandwidth knobs
- metric: frontier comparison
  - threshold: report must include slowdown versus the SRAM/NoC cap result

## Local Commands
- command: `python3 npu/eval/estimate_llm_decoder_attention_kv_onchip_service_schedule.py --repo-root . --sram-noc-constrained-json runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_kv_sram_noc_constrained_schedule__l2_decoder_attention_kv_sram_noc_constrained_schedule_llama7b_v1_r2.json --frontier-row-limit 128 --out /tmp/onchip_service.json --out-md /tmp/onchip_service.md`

## Result
- status: pending
- note: Final quality decision waits for evaluator output.
