# LLM Decoder Distribution Robustness Sweep

- `proposal_id`: `prop_l2_decoder_distribution_robustness_v1`
- `item_id`: `l2_decoder_distribution_robustness_v1`
- layer: `layer2`
- abstraction: `decoder_distribution_robustness`

## Motivation

The previous probability and fp-format sweeps showed useful rank cliffs, but
they were still measured on a tiny five-prompt setup. Approximation behavior is
expected to depend on prompt distribution, model weights, entropy, and the
top-1/top-2 logit margin. This job broadens the prompt regimes first and records
distribution rollups alongside rank metrics.

## Evaluation Shape

The evaluator should generate a fresh reference/candidate suite from
`manifest_distribution_v1.json`, then run the `decoder_distribution_robustness_v1`
rough grid. The committed result must expose:

- next-token and top-k quality per grid point
- reference entropy and top-1/top-2 logit-margin rollups
- candidate entropy, score-sum, and top-1/top-2 score-margin rollups
- per-sample miss lists

## Interpretation

This remains rough architecture evidence. A passing format on this job is not a
general LLM acceptance claim; it only tells us which approximation families
deserve narrower follow-up across larger model/weight distributions.
