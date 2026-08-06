# Strict c1_p128_b4_rr routed service power audit

- decision: `activity_backed_service_power_measured`
- promotion_gate_pass: `True`
- required_flow_variant: `decode_score_multivalue_service_c1_p128_b4_q4_rl2_rr_3000_v1_macro_conservative_c1_die_3000`
- bank3 dynamic inactivity: `[3]`
- bank3 note: No artificial activity was injected. Bank3 may remain dynamically inactive in this exact c1 workload; it is not required to toggle, while leakage remains part of routed power.
- physical status: `routed_with_electrical_caveat`
- maximum-capacitance violations: `142`
- worst maximum-capacitance slack fF: `-17.81`
- architectural use: `exploratory_routed_ppa_not_electrical_signoff`

| status | path ns | total power mW | service-window dynamic J | service-window leakage J | service-window total J |
|---|---:|---:|---:|---:|---:|
| activity_backed | 6.7148 | 0.26 | 2.094023603316061e-05 | 1.0178661571948921e-05 | 3.111889760510953e-05 |

## Macro Contract

- `fakeram45_2048x39`: `56`
- `fakeram45_64x32`: `64`
