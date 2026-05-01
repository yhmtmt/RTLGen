# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_q8_norm_distribution_broad_v2`
- `candidate_id`: `l2_decoder_q8_norm_distribution_broad_v2`

## Evaluations Consumed
- pending: `l2_decoder_q8_norm_distribution_broad_v2`
- baseline: `l2_decoder_q8_norm_distribution_robustness_v1_r4`

## Baseline Comparison
The baseline r4 result used the 12-sample distribution v1 set and found no
blocked q8 reciprocal or bf16 reciprocal rows. This follow-on job expands the
rough distribution set to 48 samples before treating the measured PPA ranking as
architecture guidance.

## Result
Pending evaluator result.

## Failures And Caveats
- The expanded dataset is still tied to the tiny decoder model.
- The result should identify distribution-sensitive rows and sample categories,
  not claim model-family robustness.

## Recommendation
Pending evaluator result.
