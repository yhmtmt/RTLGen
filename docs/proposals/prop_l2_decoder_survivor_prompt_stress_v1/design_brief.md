# LLM Decoder Survivor Prompt-Stress Sweep

- `proposal_id`: `prop_l2_decoder_survivor_prompt_stress_v1`
- `item_id`: `l2_decoder_survivor_prompt_stress_v1`
- layer: `layer2`
- abstraction: `decoder_survivor_prompt_stress`

## Motivation

The distribution robustness sweep made the prompt dependence visible and showed
clear failures for fixed final-probability q8 and fp8_e4m3. Before moving toward
hardware costing, the surviving paths need a larger prompt-stress check that
keeps the same tiny decoder model but expands prompt categories.

## Evaluation Shape

The evaluator should generate a fresh reference/candidate suite from
`manifest_prompt_stress_v1.json`, then run the
`decoder_survivor_prompt_stress_v1` rough grid. The committed result must
expose:

- next-token and top-k quality per survivor or boundary grid point
- reference entropy and top-1/top-2 logit-margin rollups
- candidate entropy, score-sum, and top-1/top-2 score-margin rollups
- per-sample miss lists

## Interpretation

This is still prompt/input distribution evidence, not model-family evidence.
Passing paths should become candidates for narrower hardware-cost work; failing
paths should remain blocked until there is a reason to revisit their format.
