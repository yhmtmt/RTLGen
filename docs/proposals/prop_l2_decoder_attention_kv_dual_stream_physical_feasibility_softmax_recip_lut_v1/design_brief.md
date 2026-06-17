# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dual_stream_physical_feasibility_softmax_recip_lut_v1`
- `title`: Softmax-recip dual-stream physical feasibility for Llama7B attention

## Problem
The subtile schedule selected `dual_mac` and reported `1575.373891 us`, but
that schedule duplicates QK and V compute resources. The architecture frontier
must account for whether that duplicated compute fits the measured logic budget.

## Hypothesis
If the duplicated compute does not fit, the correct current frontier should be
the best split/shared-MAC row that is physically feasible under the same budget.

## Evaluation Scope
- Direct comparison: best requested subtile schedule versus best area-fitting
  schedule.
- Evaluation mode: `frontier_detail`.
- Dependency: merged softmax-recip subtile pipeline schedule.
- Excluded: denser int8 compute substitution, new HBM/SRAM/NoC settings, and
  precision-quality changes.
- Follow-on: evaluate denser fused or int8 compute only if recovering dual-MAC
  remains the best architecture direction.

## Knowledge Inputs
- `npu/eval/estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py`
- softmax-recip subtile pipeline result artifact
- measured full-value tile and softmax reciprocal LUT metrics

## Candidate Direction
Convert schedule-only dual-stream rows into area-budgeted physical feasibility
rows.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-17T12:05:52Z
- note: Required before using the subtile latency as an architecture frontier.
