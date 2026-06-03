# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- `candidate_id`: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`

## Evaluations Consumed
- work item: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`
- run key: `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4_run_8c98027c0b8f2e42`
- source commit: `9d811c441c132b740a1de93b7bf203135dba392b`

## Baseline Comparison
- baseline used: prior full-value L1 clustered schedule item
  `l2_decoder_attention_kv_full_value_l1_clustered_schedule_v1`
- comparison role: broad ranking rather than paired pass/fail comparison
- local cost stack: measured compute, full-value tile, exact-int softmax weight
  generation, and local FIFO/router NoC anchors

## Result
- outcome: `ranking_recorded`
- best point: `fp16_nm1` with `flat_nomacro`
- best aggregate latency: `0.028908 ms`
- best aggregate energy: `0.0000055828 mJ`
- best critical path: `5.5570 ns`
- `fp16_nm2` was slower and higher energy in this campaign, so the measured
  local cost stack does not justify moving the current Llama7B attention
  baseline from `fp16_nm1` to `fp16_nm2`.

## Failures and Caveats
- r2 failed with evaluator termination after the estimator retained too many
  rows; the r4 retry used streaming aggregation and completed.
- SRAM capacity/service and global NoC arbitration remain analytic terms.
- Softmax wait/backpressure counters were zero in this campaign, so the result
  does not by itself stress a softmax bottleneck.
- The campaign ranks only `fp16_nm1` and `fp16_nm2`; larger parallelism still
  needs physically constrained exploration.

## Recommendation
- decision: iterate
- reason: accept the all-measured local L1 stack as the current Llama7B
  attention baseline evidence, then proceed to physically constrained SRAM and
  global-NoC modeling before claiming a final architecture frontier.
- follow-on: schedule jobs that vary die-size, SRAM capacity/service, global
  NoC topology/arbitration, and larger compute parallelism under comparable
  placement/utilization assumptions.

