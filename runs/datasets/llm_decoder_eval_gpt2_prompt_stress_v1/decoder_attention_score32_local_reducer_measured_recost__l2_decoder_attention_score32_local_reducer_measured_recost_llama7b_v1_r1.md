# Score32 Local Reducer Measured Recost

- decision: `score32_local_reducer_measured_bounded_recost_recorded`
- exact-reduction source: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_exact_reduction_recost__l2_decoder_attention_score32_exact_reduction_recost_llama7b_v1.json`
- bounded global source: `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_score32_folded_global_exact_reduction_recost__l2_decoder_attention_score32_folded_global_exact_reduction_recost_llama7b_v2_r2.json`
- reducer probe config: `runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_p53_w8/config.json`
- quality rerun required: `false`

## Routed Components

| component | critical path ns | die area um2 | core area um2 | power mW |
| --- | ---: | ---: | ---: | ---: |
| pair node | 6.5967 | 108900.0 | 96100.0 | 0.24 |
| temporal merge | 6.5967 | 108900.0 | 96100.0 | 0.24 |
| macro-only sum per cluster (52 pair + 1 temporal) | 6.5967 | 5771700.0 | 5093300.0 | 12.72 |

No routed composed-top PPA claim is made.

## Area Bounds

- synthesis-area lower bound per cluster: `3.297113` mm2 (`1652145` cells)
- top logic excluding submodules per cluster: `0.623623` mm2 (`278859` cells)
- macro-only die-area sum per cluster: `5.771700` mm2
- macro-only die-area sum scaled to 16 clusters: `92.347200` mm2
- synthesis-area lower bound scaled to 16 clusters: `52.753805` mm2

## Boundary Failures

- 10ns: `global_route_oom_boundary` via `/orfs/flow/logs/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_macro_w8/base/5_1_grt.log`
- 15ns: `macro_placer_assertion` via `/orfs/flow/logs/nangate45/attention_score32_exact_local_temporal_reducer_gqa8_physical_harness_p53_reducer_factored_hier_folded_mersenne_macro_w8/base/2_2_floorplan_macro.log`

## Service Scope

- reducer-only drain cycles: `20730`
- first output cycle: `20602`
- last output cycle: `20729`
- comparison cycle origin: `cycle0_on_first_leaf_issue_of_group0_wave0`
- includes producer compute/service: `false`

## Single-Clock Bound

| schedule term | source exact-reduction | strict no-overlap | conditional overlap |
| --- | ---: | ---: | ---: |
| per-group reduction cycles | 574 | 27632 | 23408 |
| full-layer attention-tail cycles | 574 | 110528 | 93632 |
| layer cycles | 8664 | 110730 | 93834 |
| total cycles | 277248 | 3543360 | 3002688 |
| latency us | 13488.364723 | 172387.653024 | 146083.473619 |
| token/s | 74.137971543343 | 5.800879485614 | 6.845401298494 |

- inherited single-clock bound: `48.6509` ns
- inherited clock origin: `inherited_single_clock_composed_compute_bound`
- producer barrier already includes all 8 producer waves per group: `true`
- historical tile-service term not added separately: `986` cycles per group

## Dual-Clock Component-Rate Bound

- producer clock: `48.6509` ns
- reducer/global clock: `8.0` ns
- CDC/handshake required: `true`
- measured full composition: `false`
- strict no-overlap group time: `392765.401600` ns
- strict no-overlap latency upper bound: `50588.450822` us
- strict no-overlap throughput lower bound: `19.767357642925` token/s
- conditional overlap group time: `226925.401600` ns
- conditional overlap latency lower bound: `29360.930822` us
- conditional overlap throughput upper bound: `34.058865710439` token/s

## Remaining Abstractions

- The routed composed p53 top still has only boundary evidence; no routed top-level PPA row exists.
- The 16-cluster scaling is arithmetic replication of measured/derived per-cluster evidence and is not a routed full-array composition.
- The single-clock bound inherits the 48.6509ns composed-compute clock from the earlier score32 artifact and should not be read as the standalone reducer clock.
- The dual-clock component-rate bounds require CDC plus a proved scheduler/handshake implementation and are not measured full compositions.
- No quality delta is claimed; this artifact changes timing/PPA interpretation only.
- No 328-bit transport, NoC, SRAM, or local-reducer activity-power closure is claimed here.
