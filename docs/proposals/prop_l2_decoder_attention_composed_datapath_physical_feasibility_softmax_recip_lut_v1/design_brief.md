# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_composed_datapath_physical_feasibility_softmax_recip_lut_v1`
- `title`: Softmax-recip composed dual-stream datapath feasibility for Llama7B attention

## Problem
The abstract int8-compute feasibility result recovered the `dual_mac` schedule at
`1575.373891 us`, but that result did not use the measured composed
dual-stream wrapper clock. The measured q10 composed wrapper has a slower
critical path than the source schedule clock, so the frontier ranking must use
the effective composed-clock latency.

## Hypothesis
If the measured composed wrapper clock penalty is small enough, the int8
dual-MAC point remains the best least-abstract frontier. If it is not, the
physically safer frontier may revert to the split/shared-MAC fallback until the
composed pipeline is retimed or partitioned.

## Evaluation Scope
- Direct comparison: abstract int8 dual-MAC versus measured-clock composed
  dual-MAC versus prior split/shared-MAC fallback.
- Evaluation mode: `frontier_detail`.
- Dependencies: merged softmax-recip subtile schedule, int8 feasibility result,
  measured composed wrapper PPA, and existing precision-quality gates.
- Excluded: new HBM/SRAM/NoC assumptions, new KV sharing, and real checkpoint
  quality/perplexity.

## Knowledge Inputs
- `npu/eval/estimate_llm_decoder_attention_kv_dual_stream_physical_feasibility.py`
- measured q10 composed dual-stream softmax-recip wrapper `metrics.csv`
- softmax-recip subtile pipeline schedule result
- mixed-precision and reciprocal-LUT quality decision references

## Candidate Direction
Convert the current abstract int8 dual-MAC feasibility row into a
composed-clock physical feasibility row while preserving source latency as a
diagnostic field.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-17T21:30:00Z
- note: Required before using the abstract int8 dual-MAC point as the
  least-abstract Llama7B attention frontier.
