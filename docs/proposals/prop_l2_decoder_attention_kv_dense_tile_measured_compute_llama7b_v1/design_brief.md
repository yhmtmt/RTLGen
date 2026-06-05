# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_dense_tile_measured_compute_llama7b_v1`
- `title`: `Llama7B dense tile measured compute substitution`

## Problem
The previous Llama7B compute envelope used either older nm-count compute blocks
or analytic dense-density envelopes. PR #764 measured dense FP16 GEMM tiles, but
those PPA rows have not yet been substituted into the die-budgeted Llama7B
physical-HBM memory/NoC model.

## Hypothesis
The 128-MAC dense tiles, especially `16x8_k1_p1` or `8x16_k1_p1`, should provide
a better measured compute anchor than the older nm-count blocks. The 256-MAC
`16x16_k1_p2` tile is expected to be less attractive because its measured
MAC/cycle/mm2 density dropped relative to the 128-MAC points.

## Evaluation Scope
Direct comparison set: consume the merged dense tile metrics from
`l1_npu_dense_gemm_tile_scaling_v2` and sweep die areas 100, 200, 400, 800, and
1200 mm2 with logic fractions 0.05, 0.1, 0.2, 0.4, and 0.6.

Evaluation mode: `frontier_detail`. The result is expected to select a measured
dense tile compute anchor, not prove final full-system closure.

Dependency order: this item requires merged dense tile metrics, the physical
HBM memory/NoC baseline, and the dense compute ceiling envelope.

Excluded first-stage comparisons: no new dense RTL/PPA points, no KV4/MQA
quality-risky modes, and no detailed NoC/SRAM arbitration simulation.

Follow-on broad sweep: use the selected dense anchor in clustered schedule and
memory/NoC closure.

## Knowledge Inputs
- `docs/proposals/prop_l1_npu_dense_gemm_tile_scaling_v2/analysis_report.md`
- `docs/proposals/prop_l2_decoder_attention_kv_dense_compute_ceiling_envelope_llama7b_v2/analysis_report.md`

## Candidate Direction
Extend the measured-compute estimator to load dense GEMM tile metrics and scale
replica count by the available logic area budget.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-05T12:46:48Z
- note: Proceed with a focused L2 substitution job.
