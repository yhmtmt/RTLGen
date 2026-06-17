# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_v1`
- `title`: `Endpoint/router/SRAM composition for reciprocal-LUT Llama7B frontier`

## Problem
The selected reciprocal-LUT Llama7B frontier still relies on a composition-level
assumption that endpoint, router, FIFO, and SRAM evidence can be combined at the
required width/replication without changing the bottleneck or selected point.

## Hypothesis
The endpoint/router/SRAM composition audit will confirm the q12 frontier remains
selected, or it will identify the exact missing L1 PPA evidence needed before
closing the on-chip abstraction.

## Evaluation Scope
- direct comparison set:
  - reciprocal-LUT ready/valid endpoint result
  - corrected q12 endpoint full on-chip service r2 result
  - existing router/FIFO/endpoint/SRAM evidence
- evaluation modes:
  - `frontier_detail`
  - `frontier_closure`
- dependency order:
  - depends on merged `l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_llama7b_v1`
  - requires merged inputs and materialized refs
- excluded first-stage comparisons:
  - HBM/DRAM service replacement
- follow-on broad sweep:
  - measured SRAM rebalance or HBM/DRAM service closure after composition

## Knowledge Inputs
- corrected q12 reciprocal-LUT endpoint frontier
- endpoint ready/valid result
- endpoint/router/FIFO/SRAM L1 evidence

## Candidate Direction
No new architecture point is introduced. The step reduces abstraction by
auditing whether already measured L1 blocks compose cleanly for the selected
frontier.

## Direction Gate
- status: approved
- approved_by:
- approved_utc:
- note: follow-on closure after ready/valid result
