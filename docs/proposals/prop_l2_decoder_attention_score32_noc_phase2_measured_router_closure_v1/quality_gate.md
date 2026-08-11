# Quality Gate

- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_measured_router_closure_v1`

## Required checks

- `python3 -m pytest -q tests/test_audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure.py`

## Acceptance

- the consumer rejects non-workload-complete or wrong-version Phase 2 inputs
- the consumer rejects the wrong router primitive shape
- the output labels timing as a no-reroute upper bound, router area as a lower bound, and router power as an activity-dependent estimate
- the required follow-on evidence includes release conversion and mesh rerouting at the measured router clock
- non-router closure gaps remain explicit
