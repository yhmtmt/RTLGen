# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1`
- `candidate_id`: `l2_decoder_attention_score32_local_reducer_measured_recost_llama7b_v1_r1`

## Intent
- preserve the merged exact-reduction and folded-global bounded recost artifacts
- replace only the unresolved local-reducer timing with measured folded p53 reducer-only service
- account for all 4 GQA8 groups per Llama7B layer without double-counting the inherited 986-cycle producer window
- separate inherited single-clock full-layer bounds from optimistic CDC-requiring dual-clock component-rate bounds
- consume the merged August 4, 2026 r7 macro evidence without claiming routed composed-top PPA

## Constraints
- do not dispatch physical work from this branch
- do not mutate merged evidence in place
- keep any producer/reducer overlap schedule explicitly conditional
- keep quality unchanged
