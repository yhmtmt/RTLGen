# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_recip_lut_variant_frontier_v1`
- `title`: Composed reciprocal-LUT softmax variant frontier for Llama7B attention

## Problem
The current composed datapath feasibility result uses the q10 reciprocal-LUT
wrapper only. Existing PPA data also includes q8 and q12 reciprocal-LUT
wrappers, and the measured q8 wrapper has lower area, power, and critical path
than q10. The frontier should compare these measured variants directly instead
of keeping q10 as an implicit fixed choice.

## Evaluation Scope
- Compare q8/q10/q12 measured composed dual-stream reciprocal-LUT wrappers.
- Keep the upstream softmax-recip subtile schedule fixed.
- Keep the existing proxy quality/equivalence evidence as provenance.
- Report source latency and effective measured-wrapper latency separately.

## Exclusions
- No new OpenROAD run.
- No memory/NoC/HBM assumption changes.
- No claim of final real-checkpoint Llama7B quality closure.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-17T21:45:00Z
- note: Required because q8/q10/q12 measured wrapper PPA is already available
  and materially changes the composed frontier ranking.
