# Proposal Overview

- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_measured_router_closure_v1`
- scope: consume the corrected workload-complete Phase 2 NoC schedule and the measured single-router Phase 1 primitive
- output: a conservative no-reroute timing upper bound, a router-area lower bound, and an activity-dependent router-power component estimate
- excluded: aggregate 4x4 placed-mesh PPA claims, ranking updates, DB writes, and job dispatch
