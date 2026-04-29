# Decoder Normalization PPA Calibration

- calibration_status: `partial_integer_reciprocal_primitives_calibrated`
- platform: `nangate45`
- source_sweep: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_quality_sweep__l2_decoder_q8_normalization_frontier_v1.json`
- proposal: `prop_l1_decoder_normalization_arithmetic_calibration_v1`

## Selected Primitive Evidence

| role | block | critical_path_ns | die_area | total_power_mw | metrics_csv |
|---|---|---:|---:|---:|---|
| `q8_reciprocal_multiplier_16u` | `mult16u_booth4_koggestone` | 0.1941 | 3487.49 | 0.00364 | `runs/designs/multipliers/mult16u_booth4_koggestone_wrapper/metrics.csv` |
| `q8_accumulator_adder_64u` | `adder_koggestone_64u` | 0.2225 | 3074.7 | 0.00104 | `runs/designs/prefix_adders/adder_koggestone_64u_wrapper/metrics.csv` |

## Candidate Calibration

| template | status | exact-safe | reciprocal bits | primitive critical_path_ns sum | primitive area sum | primitive power sum | gaps |
|---|---|---:|---:|---:|---:|---:|---|
| `grid_approx_pwl_bf16_path` | `unmeasured_gap` | yes |  |  |  |  | `bf16 reciprocal path`, `bf16 multiply/round/convert datapath`, `integrated normalization datapath routing/control` |
| `grid_approx_pwl_in_q8_w_q8_norm_exact` | `unmeasured_gap` | yes |  |  |  |  | `integer exact divider/reciprocal datapath` |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q10` | `integer_reciprocal_primitives_calibrated_not_integrated_datapath` | yes | 10 | 0.4166 | 6562.195525 | 0.00468 | `integrated normalization datapath routing/control`, `pipeline/register placement around reciprocal multiply and accumulation` |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q12` | `integer_reciprocal_primitives_calibrated_not_integrated_datapath` | yes | 12 | 0.4166 | 6562.195525 | 0.00468 | `integrated normalization datapath routing/control`, `pipeline/register placement around reciprocal multiply and accumulation` |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q14` | `integer_reciprocal_primitives_calibrated_not_integrated_datapath` | yes | 14 | 0.4166 | 6562.195525 | 0.00468 | `integrated normalization datapath routing/control`, `pipeline/register placement around reciprocal multiply and accumulation` |
| `grid_approx_pwl_in_q8_w_q8_norm_recip_q16` | `integer_reciprocal_primitives_calibrated_not_integrated_datapath` | yes | 16 | 0.4166 | 6562.195525 | 0.00468 | `integrated normalization datapath routing/control`, `pipeline/register placement around reciprocal multiply and accumulation` |

## Interpretation

- The q8 reciprocal path now has measured Nangate45 multiplier and accumulator/adder primitive evidence.
- The q8 exact-normalization row is still blocked for hardware acceptance by an unmeasured exact divider/reciprocal datapath.
- The bf16 reciprocal PWL anchor is still blocked for hardware acceptance by unmeasured bf16 reciprocal and multiply/convert datapaths.
- The q8 reciprocal q10/q12/q14/q16 rows share the same measured primitive envelope in this calibration. Under that envelope, physical PPA does not justify preferring q10 over q12/q14/q16; q10 remains a quality/minimum-precision choice from the prompt-stress sweep.

## Next Step

- Use the calibrated primitive axes to plan an integrated q8 reciprocal-normalization datapath measurement.
- Do not compare q8 reciprocal against bf16 as a hardware decision until bf16 reciprocal/multiply primitives are also measured.
