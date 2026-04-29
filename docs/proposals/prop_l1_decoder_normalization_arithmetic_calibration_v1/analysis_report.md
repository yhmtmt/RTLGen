# Analysis Report

## Candidate
- `proposal_id`: `prop_l1_decoder_normalization_arithmetic_calibration_v1`
- `candidate_id`: `l1_decoder_norm_q8_recip_mult_calibration_v1_r2`
- `candidate_id`: `l1_decoder_norm_accumulator_adder_calibration_v1_r2`

## Evaluations Consumed
- `l1_decoder_norm_q8_recip_mult_calibration_v1_r2`
- review: PR #281
- source commit: `ea6095808f683c26979575365f9a5c4249470a05`
- `l1_decoder_norm_accumulator_adder_calibration_v1_r2`
- review: PR #282
- source commit: `ea6095808f683c26979575365f9a5c4249470a05`

## Calibrated Primitive Evidence
- multiplier artifact: `control_plane/shadow_exports/l1_promotions/l1_decoder_norm_q8_recip_mult_calibration_v1_r2.json`
- adder artifact: `control_plane/shadow_exports/l1_promotions/l1_decoder_norm_accumulator_adder_calibration_v1_r2.json`
- synthesis report: `runs/datasets/llm_decoder_eval_tiny_v1/decoder_norm_ppa_calibration__prop_l1_decoder_normalization_arithmetic_calibration_v1.md`
- selected q8 reciprocal multiplier primitive: `mult16u_booth4_koggestone`, Nangate45, `critical_path_ns=0.1941`, `die_area=3487.493025`, `total_power_mw=0.00364`
- selected q8 accumulator adder primitive: `adder_koggestone_64u`, Nangate45, `critical_path_ns=0.2225`, `die_area=3074.7025`, `total_power_mw=0.00104`

## Result
- result: `promote`
- confidence level: merged accepted L1 evidence
- architecture conclusion robustness: partial primitive-level calibration, not full datapath PPA
- summary: The q8 reciprocal normalization path now has measured Nangate45 multiplier and accumulator/adder primitive evidence. The evidence replaces the previous hand-written planning proxy for those primitive terms, but does not yet calibrate the exact divider, bf16 reciprocal/multiply path, or integrated normalization datapath routing/control.

## Interpretation
- The q8 reciprocal q10/q12/q14/q16 rows all use the same current 16-bit multiplier envelope plus the same accumulator primitive in this synthesis.
- Under that envelope, physical primitive PPA does not justify preferring q10 over q12/q14/q16. q10 remains a quality/minimum-precision decision from the prompt-stress sweep, not a measured PPA win over wider reciprocal settings.
- The q8 exact-normalization row remains a hardware-acceptance gap because the exact divider/reciprocal datapath has not been measured.
- The bf16 reciprocal PWL anchor remains a hardware-acceptance gap because the bf16 reciprocal and multiply/convert datapaths have not been measured.

## Recommendation
- `promote`
- reason: Accepted Layer 1 physical metrics were merged for both the multiplier and accumulator/adder primitive jobs.
- next_action: plan an integrated q8 reciprocal-normalization datapath measurement, and separately measure bf16 reciprocal/multiply primitives before making q8-versus-bf16 hardware decisions.
