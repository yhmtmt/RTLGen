# Llama7B operational component frontier

- decision: `operational_component_area_timing_recosted_energy_retained`
- recommended candidate: `score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components`
- latency: `1595.42090302109` us
- throughput: `626.793843622331` token/s
- retained activity-backed energy: `137.330868813197` mJ/token
- embodied area: `325.5239481009` mm2
- vectorless-power energy promotion: `blocked`

| candidate | latency us | token/s | energy mJ/token | embodied mm2 | timing ok |
|---|---:|---:|---:|---:|---|
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components | 1595.42090302109 | 626.793843622331 | 137.330868813197 | 325.5239481009 | True |
| score32_separated_zero_tail_two_pass_conservative_per_head_iterdiv_operational_components | 1600.407500163976 | 624.840860779233 | 137.755482392336 | 325.5239481009 | True |
| score32_separated_zero_tail_two_pass_nominal_shared_iterdiv_operational_components | 1744.22090302109 | 573.32187584035 | 137.330868813197 | 321.9923971009 | True |
| score32_separated_zero_tail_two_pass_conservative_shared_iterdiv_operational_components | 1749.207500163976 | 571.687464126616 | 137.755482392336 | 321.9923971009 | True |
