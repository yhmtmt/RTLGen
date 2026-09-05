# Llama7B Physically Credible Pareto Audit

- decision: `two_provisional_quality_backed_component_composed_pareto_points`
- scope: `attention_centered_not_full_model`
- promotion gate: `False`

| credible Pareto point | family | latency us | token/s | energy mJ/token | component area mm2 | die envelope mm2 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `score32_exp_lut_schedule_wrapper_hbm_controller_replay_best` | `score32_exp_lut_div` | 12814.258 | 78.038 | 467.191 | 296.826 | 800.000 |
| `die1200_dense_gemm_16x8_k1_p1_mac132736_lat1872.29_hbm0.465654_tt512` | `measured_exact_fp16_gqa8_kv8` | 72544.062 | 13.785 | 81.664 | 479.602 | 1200.000 |

## RMSNorm Serialized-Latency Robustness

- score32 remains latency anchor across envelope: `True`
- best adjusted latency: `13487.008 us`
- worst adjusted latency: `14920.258 us`
- nearest other Pareto latency: `72544.062 us`
- claim scope: serialized latency only; no norm area or energy promotion

## Energy-Axis Uncertainty

- status: `recorded_energy_tradeoff_not_activity_closed`
- recorded score32/reference ratio: `5.721x`
- score32 reduction required to tie if reference is unchanged: `82.520%`
- activity-closed Pareto status: `unproven`
- reason: The selected frontier has no score32_activity_power_json input. Its recorded energy ratio is a break-even sensitivity, not an activity-backed dominance claim.

## Excluded Points

| candidate | reasons |
| --- | --- |
| `die800_dense_gemm_int8_16x8_k1_p1_rep855_lat1575.37_hbm0.983398_tt1024` | not_promotable, not_quality_backed |
| `physical_hbm_gqa8_kv8_service_frontier` | not_promotable, not_quality_backed |

## Evidence Limits

- latency: component-composed attention-centered estimate
- area: component-composed compute/controller area is the dominance objective; die area is retained only as a capacity envelope, and RMSNorm area is not yet included
- energy: not activity-backed in this frontier; schedule-wrapper activity input is absent

## Promotion Blockers

- the frontier energy objective does not consume schedule-wrapper post-route activity power
- transformer RMSNorm latency is excluded and its routed area/activity/overlap are open
- NoC and selected SRAM hierarchy lack matched workload-backed routed activity power
- the architecture is component-composed rather than a full-chip routed implementation

Among quality-backed promotable rows, score32 is the latency/area point and measured exact FP16 is the energy point; neither dominates the other. These are provisional component-composed Pareto anchors, not final full-model PPA points. Non-promotable abstract or quality-invalid rows are never allowed to dominate the credible set.
