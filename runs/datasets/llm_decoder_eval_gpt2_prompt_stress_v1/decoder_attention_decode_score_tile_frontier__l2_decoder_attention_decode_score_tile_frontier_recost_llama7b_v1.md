# Llama7B decode-shaped M1x8 score-tile frontier

- decision: `decode_shaped_m1x8_schedule_and_area_recosted_energy_retained`
- best throughput: `669.792507491203` token/s
- best throughput area: `482.5046840209` mm2
- best area: `323.4220925409` mm2
- best-area throughput: `570.666388631788` token/s
- activity-backed decode-tile energy promotion: `blocked`

| candidate | token/s | latency us | energy mJ/token | area mm2 | area fit |
|---|---:|---:|---:|---:|---|
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_scalar_area_budget | 669.792507491203 | 1492.99968096931 | 137.330868813197 | 482.5046840209 | True |
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_packed_area_budget | 653.881013825514 | 1529.330228063247 | 137.330868813197 | 482.5029291009 | True |
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_scalar_throughput_matched | 630.68989653931 | 1585.565276195402 | 137.330868813197 | 344.0081203409 | True |
| score32_separated_zero_tail_two_pass_nominal_per_head_iterdiv_operational_components_decode_m1x8_scalar_nominal_peak | 623.621289340162 | 1603.537302355529 | 137.330868813197 | 326.9536435409 | True |
| score32_separated_zero_tail_two_pass_nominal_shared_iterdiv_operational_components_decode_m1x8_scalar_nominal_peak | 570.666388631788 | 1752.337302355529 | 137.330868813197 | 323.4220925409 | True |
