# Two-Pass Integrated Frontier Ranking

- decision: `two_pass_measured_components_integrated_frontier_ranked`
- recommended candidate: `score32_zero_tail_two_pass_nominal_per_head_iterdiv`
- recommended latency us: `12940.224364999998`
- minimum-area candidate: `score32_zero_tail_two_pass_nominal_shared_iterdiv`
- quality status: `mixed_int8_generation_quality_pass`

| candidate | latency us | token/s | energy mJ/token | logic + score macro mm2 |
|---|---:|---:|---:|---:|
| score32_zero_tail_two_pass_nominal_per_head_iterdiv | 12940.224364999998 | 77.278412784306 | 467.469446724434 | 367.1087352009 |
| score32_zero_tail_two_pass_conservative_per_head_iterdiv | 12979.852372999998 | 77.042478701849 | 467.469446724434 | 367.1087352009 |
| score32_zero_tail_two_pass_nominal_shared_iterdiv | 13089.024365 | 76.399888342633 | 467.469446724434 | 363.5771842009 |
| score32_zero_tail_two_pass_conservative_shared_iterdiv | 13128.652372999999 | 76.169280104984 | 467.469446724434 | 363.5771842009 |

## Assumptions

- The source compute/controller row remains measured evidence; the two-pass service is added rather than silently replacing unseparated logic area.
- Only the score-SRAM recost latency delta is transferred onto the current controller-replay frontier, preserving measured controller overhead.
- Divider active energy is charged once per head, so sharing changes latency and area but not total divider work energy.
- The score SRAM macro area is reported separately from its placement envelope to avoid double counting the fixed die budget.
- HBM service and score-SRAM floorplan PNR remain explicit abstractions.
