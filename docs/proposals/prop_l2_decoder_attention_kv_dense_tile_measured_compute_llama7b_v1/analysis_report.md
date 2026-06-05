# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`

## Evaluations Consumed
- pending evaluator run

## Baseline Comparison
- baseline: `l2_decoder_attention_kv_measured_compute_llama7b_v1`
- comparison: dense tile measured compute source versus older nm-count measured compute source

## Result
- pending evaluator result

## Failures and Caveats
- Dense tile replica scaling does not yet model global command routing, placement, or inter-tile composition overhead.
- SRAM and NoC service remain L2 model assumptions.

## Recommendation
- pending evaluator result
