# Quality Gate

The evaluation should:

- regenerate reference and candidate artifacts from
  `runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v2.json`
- run the existing `decoder_q8_normalization_frontier_v1` rough grid
- report next-token and top-k preservation by row
- rank exact-safe rows with measured Nangate45 datapath metrics where available
- explicitly list any blocked rows and mismatch sample ids

Acceptance for this exploratory step is not "choose final q8 or bf16." Acceptance
is a complete broad-ranking artifact that tells us whether the current exact-safe
frontier survives a larger rough prompt distribution.
