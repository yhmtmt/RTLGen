# Quality Gate

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_v1`
- `candidate_id`: `l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_llama7b_v1`

## Required Evidence
- The generated command must consume the measured q10 composed dual-stream
  softmax-recip wrapper metrics.
- The JSON result must report effective `best_feasible_latency_us` after
  composed clock scaling.
- The JSON result must preserve `best_feasible_source_latency_us` for the
  original schedule latency.
- The result consumer must record the composed evidence and source references.

## Pass Criteria
- `decision` is recorded.
- Effective latency is not silently replaced by source schedule latency when a
  composed wrapper clock is present.
- Existing mixed-precision quality and reciprocal-LUT decision references are
  preserved as input evidence.
