# Strict c1_p128_b4_rr routed service power audit

- decision: `activity_power_rejected_no_gated_candidate`
- promotion_gate_pass: `False`
- required_flow_variant: `decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1_macro_conservative_c1_die_3000`
- bank3 dynamic inactivity: `[3]`
- bank3 note: No artificial activity was injected. Bank3 may remain dynamically inactive in this exact c1 workload; it is not required to toggle, while leakage remains part of routed power.
- physical status: `routed_with_electrical_caveat`
- maximum-capacitance violations: `142`
- worst maximum-capacitance slack fF: `-17.81`
- architectural use: `exploratory_routed_ppa_not_electrical_signoff`

| status | path ns | total power mW | service-window dynamic J | service-window leakage J | service-window total J |
|---|---:|---:|---:|---:|---:|
| None | None | None | None | None | None |

## Macro Contract

- `fakeram45_2048x39`: `56`
- `fakeram45_64x32`: `64`

## Failure

- type: `ValueError`
- summary: postroute power total_w does not match internal+switching+leakage
