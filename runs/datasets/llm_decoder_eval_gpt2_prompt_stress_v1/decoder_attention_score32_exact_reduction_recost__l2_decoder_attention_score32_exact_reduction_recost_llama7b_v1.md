# Score32 Exact Reduction Recost

- decision: `score32_exact_reduction_schedule_recost_recorded`
- source recost: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_composed_datapath_physical_feasibility__l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1.json`
- banked config: `runs/designs/npu_blocks/attention_score32_exact_banked_finalized_tree_c16_r2_l8_b59/config.json`
- analytical service: `npu.sim.perf.attention_exact_partial.exact_banked_finalized_tree_full_wave_saturated_service`
- source item: `l2_decoder_attention_composed_datapath_score32_exp_lut_div_schedule_wrapper_recost_llama7b_v1`
- recorded exact output hash: `027dd06c1e4e1bc77636eb4041aa7efd4fd6e55a090b337a6d33f78da89f65bd`
- recorded probe command: `python npu/eval/probe_attention_score32_exact_banked_finalized_tree.py --clusters 16 --heads 32 --divider-lanes 8 --finalizer-banks 59 --saturated --root-ready-pattern 1 --json`

| metric | source | corrected |
| --- | ---: | ---: |
| reduction cycles | 141 | 574 |
| layer cycles | 8231 | 8664 |
| total cycles | 263392 | 277248 |
| latency us | 12814.257853 | 13488.364723 |
| adjusted latency us if feasible | 12814.257853 | 13488.364723 |
| token/s | 78.03807 | 74.13797 |

## Full-Wave Service

- config: `c16/r2/l8/b59`
- no-stall full-wave root service: first `62`, last `573`, drain `574`, interval `511`, cycles/beat `1.000000`, dispatch stall `0`
- divider contract stays distinct: iterations `57`, output latency `58`, reaccept `59`
- schedule interpretation: producer arrival timing and overlap with the reducer are not embodied here; the 574-cycle drain is applied after tile waves as a conservative serialized-stage schedule

## Remaining Abstractions

- Exact reducer PPA remains unclosed; this recost changes schedule cycles only.
- Exact reducer activity energy remains unclosed; no reduction toggle-energy closure is claimed here.
- 328-bit exact transport, NoC, and SRAM composition remain unclosed.
- Producer arrival timing and overlap with the reducer are not embodied here; adding the 574-cycle drain after tile waves is a conservative serialized-stage schedule.
