# Quality Gate

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_v1`
- `candidate_id`: `l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_llama7b_v1`

## Required Evidence
- The generated command consumes q8, q10, and q12 composed wrapper metrics.
- The result reports the selected reciprocal-LUT variant label.
- Effective latency is based on measured wrapper clock, not source schedule
  latency.
- Existing reciprocal-LUT quality evidence is preserved as provenance.

## Pass Criteria
- A physically feasible best row is recorded.
- The selected variant label is present in the diagnosis and summary.
- The baseline q10 composed route continues to work unchanged.
