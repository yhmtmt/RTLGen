# Design Brief

## Proposal
- `proposal_id`: `prop_l1_decoder_attention_endpoint_router_segmented_noc_ppa_v1`
- `title`: `Measure segmented/narrower NoC router/FIFO alternatives for Llama7B endpoint composition`

## Problem
- The selected Llama7B endpoint composition uses a 2048-bit link, but flat 2048-bit router/FIFO primitives failed physical boundary runs. Continuing to use flat 2048-bit PPA would overstate closure.

## Hypothesis
- 128-bit and 256-bit lane primitives can provide concrete PPA inputs for segmented or narrower scheduled NoC interpretations while avoiding the known flat 2048-bit failure point.

## Evaluation Scope
- Direct comparison set: 128-bit and 256-bit router/FIFO primitive wrappers.
- Evaluation mode: `frontier_closure`.
- Dependency: `l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r3` must be merged.
- Excluded first-stage comparison: placed aggregate segmented NoC wrapper RTL.
- Follow-on: re-rank the composition using 16x128, 8x256, and narrower-link schedule interpretations.

## Knowledge Inputs
- PR #896 composition audit.
- `control_plane/shadow_exports/l2_decisions/l2_decoder_attention_kv_endpoint_router_sram_composition_softmax_recip_lut_llama7b_v1_r3.json`
- Existing NoC primitive metrics under `runs/designs/noc`.

## Candidate Direction
- Refresh proposal-linked lane primitive PPA evidence under a dedicated sweep tag.

## Direction Gate
- status: pending
- approved_by:
- approved_utc:
- note: Ready for L1 sweep dispatch after merge.
