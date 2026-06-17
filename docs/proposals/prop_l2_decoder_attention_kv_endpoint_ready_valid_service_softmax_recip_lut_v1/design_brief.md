# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_endpoint_ready_valid_service_softmax_recip_lut_v1`
- `title`: `Ready/valid endpoint service for reciprocal-LUT Llama7B frontier`

## Problem
The current selected Llama7B reciprocal-LUT endpoint frontier includes explicit
on-chip service policy fields, but the endpoint queue/backpressure behavior is
still represented analytically. The next abstraction to close is whether the
selected endpoint queue sizes, packet payload, and producer/consumer rates are
compatible with the concrete `onchip_service_endpoint` ready/valid model.

## Hypothesis
The selected q12 frontier remains the best point when endpoint queueing is
checked with finite ready/valid queues, because the selected row already uses
`prefetch_overlap`, `locality_first`, 2048-byte endpoint/bank queues, and a
shared-path service bottleneck that should not require a different topology.

## Evaluation Scope
- direct comparison set:
  - selected q12 reciprocal-LUT endpoint full on-chip service row
  - concrete endpoint ready/valid finite-queue probe
- evaluation modes:
  - `frontier_detail`
  - `frontier_closure`
- dependency order:
  - depends on merged `l2_decoder_attention_kv_endpoint_full_onchip_service_schedule_softmax_recip_lut_llama7b_v1_r2`
  - requires merged inputs and materialized refs
- excluded first-stage comparisons:
  - HBM/DRAM replacement
  - full router/SRAM composition audit
- follow-on broad sweep:
  - endpoint/router/SRAM composition audit if the ready/valid probe succeeds

## Knowledge Inputs
- corrected r2 decision artifact for q12/q10/q8 profile coverage
- `onchip_service_endpoint` RTL and ready/valid probe script
- prior non-recip-LUT ready/valid result

## Candidate Direction
No architecture parameter is changed in this step. The step replaces a portion
of the endpoint-service abstraction with a concrete ready/valid endpoint probe.

## Direction Gate
- status: approved
- approved_by:
- approved_utc:
- note: focused closure step after corrected q12 reciprocal-LUT frontier
