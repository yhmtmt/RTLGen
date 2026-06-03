# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_physical_hbm_compute_sensitivity_llama7b_v2`
- `title`: `Llama7B physical HBM compute sensitivity`

## Problem
The previous Llama7B frontier used measured local L1 costs, but the compute
throughput supplied to the high-level schedule was still a planning parameter.
The current `nm1` physical datapath is much smaller than the compute required
by the Llama7B-scale attention frontier, so the memory-bound conclusion must be
checked across a practical compute-throughput range.

## Hypothesis
There is a compute floor above which native-GQA KV8 131k decode attention is
dominated by HBM/SRAM/NoC service rather than local compute. Below that floor,
small compute arrays remain compute-bound and should not be used to argue that
HBM is the dominant system bottleneck.

## Evaluation Scope
- direct comparison set: die area 400, 800, and 1200 mm2; native GQA8 KV8;
  8 HBM stacks at 9000 MT/s and 0.75 efficiency; tile sizes 512 and 1024;
  SRAM fractions and bank counts in the high-SRAM practical region; MAC/cycle
  values 32768, 65536, 131072, 262144, and 524288; vector-op/cycle values
  8192, 16384, 32768, and 65536.
- evaluation mode: `broad_ranking` over an analytic physical HBM/NoC planning
  model paired with the merged all-measured local L1 baseline.
- dependency order: requires
  `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4` merged and
  materialized before review.
- excluded first-stage comparisons: no new RTL/PnR, no full HBM timing model,
  no routed global NoC, no MQA/KV4 quality-changing variants, and no Llama7B
  training recovery.
- follow-on broad sweep: use the boundary to choose concrete clustered compute
  RTL, then sweep NoC hops/bandwidth and SRAM/HBM balance.

## Knowledge Inputs
- Prior merged all-measured local L1 result:
  `l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1_r4`.
- Current discussion: compute throughput must be interpreted under die area,
  SRAM capacity, HBM bandwidth, and NoC assumptions before drawing Llama7B
  architecture conclusions.

## Candidate Direction
Keep the all-measured local L1 cost basis and sweep larger effective compute
throughput in the physical HBM planning model. Use the resource classification
from the model to identify which compute points are still compute-bound.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-03T06:46:51Z
- note: The job is bounded to a planning-model sweep and does not promote a new
  hardware architecture by itself.
