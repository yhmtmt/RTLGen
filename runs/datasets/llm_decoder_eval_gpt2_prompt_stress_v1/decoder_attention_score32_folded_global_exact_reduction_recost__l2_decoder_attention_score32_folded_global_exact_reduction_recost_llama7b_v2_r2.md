# Folded Global Exact Reduction Recost

- decision: `folded_global_exact_reduction_bounded_recost_recorded`
- superseded timing source: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_recost__l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json`
- cadence audit: `npu/docs/generated/llama7b_score32_exact_hierarchy_cadence_audit_v3.json`
- quality rerun required: `false`

## Measured Component Estimate

| component | critical path ns | area um2 | power mW |
| --- | ---: | ---: | ---: |
| folded c16 tree | 7.9837 | 789495.0 | 4.15000 |
| root finalizer L8 x4 | 3.4350 | 97244.4 | 0.05120 |
| bank control b4 | 2.8512 | 5812.37 | 0.00176 |
| composed estimate | 7.9837 | 892551.77 | 4.20296 |

Vectorless power only. No composed-route claim is made.

## Schedule Bounds

- corrected worst-loaded single-datapath wave: `1536` cycles for block counts `[2, 1, 1, 1]`
- conservative per-cluster barrier: `528` cycles per wave/group, `4224` cycles across 8 waves
- folded c16 global tree service: `128` beats, first `80`, last/drain `2620`, II `20`
- measured finalizer contract: per-bank output latency `58`, accept interval `59`, minimum banks `3`, measured point `b4`, same-bank revisit `80`
- composed global final output drain: `2678` cycles
- strict serialized bound: `6902` cycles per group, `27608` cycles for 4 groups
- conditional overlap margin: `1546` cycles, status `not_established`

Do not start the global folded tree before the local 53/54-way group-major reducer emits valid per-cluster group aggregates.

## Decision

- The measured folded global tree plus measured L8/b4 finalizer path is physically plausible.
- It is not necessarily throughput-dominant under the current evidence.
- The immediate unresolved frontier is the local p53/p54 persistent reducer and the overlap scheduler.

## Remaining Abstractions

- The local 53/54-way exact reducer that emits one valid group aggregate per cluster is still unmeasured.
- Safe overlap between successive groups is not established; the 1546-cycle margin is conditional only.
- The composed PPA estimate is a vectorless sum of standalone component rows and not a routed composed macro.
- No 328-bit transport, NoC, SRAM, or local-reducer activity-power closure is claimed here.
