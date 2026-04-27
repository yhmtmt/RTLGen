# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_llm_attention_tail_v1`
- `candidate_id`: `measurement_gate_l2_llm_attention_tail_v1_r1`

## Evaluations Consumed
- work item: `l2_llm_attention_tail_v1_nangate45_r1`
- run key: `l2_llm_attention_tail_v1_nangate45_r1_run_be2fd33c8cfd917e`
- source commit: `e0010e569dcbf4f4da47802bfed745545e49e563`
- review metadata commit: `813d7a7166e961da4105e4c326b6ab14120356db`
- report: `runs/campaigns/npu/e2e_eval_llm_attention_tail_v1__l2_llm_attention_tail_v1_nangate45_r1/report.md`
- decision artifact: `control_plane/shadow_exports/l2_decisions/l2_llm_attention_tail_v1_nangate45_r1.json`

## Baseline Comparison
This proposal uses `broad_ranking`; it does not define a paired baseline item.
The result ranks existing architecture points across the attention-tail model
set.

Key aggregate result:

- rank 1: `fp16_nm1` / `flat_nomacro`
- mean latency: `0.0198892 ms`
- mean throughput: `85743.733197 infer/s`
- mean energy: `3.8410420824e-06 mJ`
- mean critical path: `5.557037432204143 ns`
- softmax engine occupancy mean: `0.10425980225607101`
- softmax backpressure: `0 events`, `0 ns`

`fp16_nm2` / `flat_nomacro` is on the Pareto set because it has lower flow
runtime, but it consumes more energy than `fp16_nm1` / `flat_nomacro` under the
weighted latency+energy objective.

## Result
- outcome: measurement collected
- confidence level: medium
- proposal judgment: iterate
- reason: the run produced complete attention-tail evidence, but the broad
  ranking does not by itself justify a new architecture promotion
- mapper optimization room: still open; the measured softmax backpressure is
  zero in this workload set, so a follow-up should stress overlap/backpressure
  before claiming a softmax-specific hardware bottleneck

## Failures and Caveats
- no campaign command failures were recorded
- the proposal has no paired baseline, so `proposal_outcome` is reported as
  unavailable in the generated review artifact
- equal latency across architecture points means the ranking is driven mostly by
  energy, power, critical path, and flow-runtime side metrics

## Recommendation
- decision: iterate
- next action: create a focused follow-up proposal that uses this evidence to
  stress softmax scheduling overlap and backpressure, then compare the targeted
  mapper or architecture change against the current `fp16_nm1` / `flat_nomacro`
  reference
