# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_exact_probability_path_v1`
- `candidate_id`: `l2_decoder_exact_probability_path_v1`

## Evaluations Consumed
- local regenerated candidate artifacts only; evaluator item pending

## Baseline Comparison
- baseline: `l2_decoder_contract_eval_confirm_v1`
- prior exact/top-k rates: `0.8`
- local exact probability-path exact/top-k rates: `1.0`

## Result
- local win; evaluator confirmation pending

## Failures and Caveats
- exact probability math is a quality-preserving reference candidate, not a
  hardware approximation acceptance
- selected tensor trace hashes remain intentionally different because candidate
  selected tensors are still quantized for inspection

## Recommendation
- submit paired evaluator item before promotion
