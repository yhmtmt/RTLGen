# Quality Gate

## Proposal
- `proposal_id`: `prop_l2_decoder_q8_norm_distribution_robustness_v1`
- `title`: `Decoder q8/bf16 normalization distribution robustness`

## Checks
- next-token match:
  - threshold: exact-safe rows must match all distribution samples
- top-k containment:
  - threshold: exact-safe rows must contain the reference id in top-k for all distribution samples
- measured PPA ranking:
  - threshold: rows without merged PPA remain fallback-ranked and must not be treated as measured winners

## Local Commands
- `python3 npu/eval/sweep_llm_decoder_candidate_quality.py --dataset-manifest runs/datasets/llm_decoder_eval_tiny_v1/manifest_distribution_v1.json --rough-grid decoder_q8_normalization_frontier_v1 --out-dir /tmp/decoder_q8_norm_distribution --out /tmp/decoder_q8_norm_distribution.json`
- `python3 npu/eval/estimate_llm_decoder_q8_norm_frontier.py --sweep /tmp/decoder_q8_norm_distribution.json --out /tmp/decoder_q8_norm_distribution_frontier.json --out-md /tmp/decoder_q8_norm_distribution_frontier.md`

## Result
- status: pending remote evaluation
- note: consume the merged review artifact before selecting a follow-on architecture direction.
