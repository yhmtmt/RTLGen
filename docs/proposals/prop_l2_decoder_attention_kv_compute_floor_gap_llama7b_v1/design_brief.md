# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_compute_floor_gap_llama7b_v1`
- `title`: `Llama7B attention/KV compute floor gap`

## Problem
The merged physical-HBM compute sensitivity found that Llama7B 131k attention
becomes HBM-bound only once compute reaches roughly 131072 MAC/cycle. Existing
measured NPU compute substitution results top out much lower. Before adding
more detailed SRAM/NoC arbitration, we need to quantify that gap.

## Hypothesis
The current measured NPU compute density is below the first HBM-bound floor by
multiple factors, so the next work should target compute density and clustered
compute structure before deeper NoC simulation.

## Evaluation Scope
- direct comparison set: HBM-bound floor from
  `l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2` against
  measured compute and measured partition artifacts.
- target points: 131072, 262144, and 524288 MAC/cycle.
- die sizes: 400, 800, and 1200 mm2.
- logic fractions: 0.2, 0.4, and 0.6.
- excluded first-stage comparisons: no new RTL/PnR, no HBM controller timing,
  and no full NoC arbitration.

## Knowledge Inputs
- PR #750 compute-sensitivity result.
- Merged measured-compute and measured-compute-partition Llama7B reports.

## Candidate Direction
Use this as a planning gate. If the gap is large, define a denser compute
architecture target instead of deepening the memory/NoC model immediately.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-03T07:12:45Z
- note: This is a low-cost analytic comparison over merged artifacts.
