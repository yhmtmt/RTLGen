# Design Brief

- `proposal_id`: `prop_l2_decoder_attention_score32_noc_phase2_measured_router_closure_v1`
- date: `2026-08-11`

## Goal

Bind the corrected `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1` schedule to the measured `l1_segmented_xy_mesh_noc_phase1_v1` router primitive without over-claiming full-mesh physical closure.

## Boundaries

- Accept only the corrected Phase 2 v2 workload-complete schedule artifact.
- Accept only the exact five-port 256-bit VC4 depth-4 segmented router primitive from Phase 1.
- Bound NoC drain time without rerouting by applying the slower of the schedule NoC clock and measured router critical path to the existing absolute cycle count.
- Report router area as a lower bound and router power as an activity-dependent component estimate across the explicit mesh node count.
- Require a follow-on release conversion and mesh rerun at the measured clock before treating timing as exact.
- Keep aggregate wiring, congestion, endpoint SRAM/queues, HBM/DRAM, and root-finalizer internal compute explicit.

## Deliverables

- `npu/eval/audit_llm_decoder_attention_score32_noc_phase2_measured_router_closure.py`
- focused unit tests for the consumer
- proposal docs describing the bounded closure step and its remaining abstractions
