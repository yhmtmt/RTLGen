# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- `title`: Llama7B clustered attention schedule with measured L1 local costs

## Problem
The previous clustered Llama7B attention frontier treated the local tile,
reducer, FIFO, and router logic as free. That made cluster-count decisions
optimistic because only replicated compute-array PPA consumed the logic budget.

## Hypothesis
Charging measured folded tile/reducer and FIFO/router costs per cluster will
show whether the current clustered frontier is stable, or whether local control
and interconnect costs push the design toward fewer clusters or smaller local
profiles.

## Evaluation Scope
- Llama7B proxy at 131k context, native GQA8, KV8.
- Measured compute-array candidates selected by `compute_stability_cmp33`.
- Measured L1 local-cost profiles from PR #719 and PR #720.
- Die sizes: 200, 400, 800, and 1200 mm2.
- SRAM fractions: 0.4 and 0.6; logic fractions: 0.1 and 0.2.
- Cluster counts: 1, 2, 4, 8, and 16.
- NoC bandwidths: 8192 and 32768 bytes/cycle; hops: 1, 2, and 4.
- Reduction strategies: `owner_cluster` and `cluster_tree`.

## Exclusions
- New RTL/PPA runs.
- Full softmax-weighted value datapath closure.
- Cycle-accurate NoC/SRAM arbitration.
- Quality-degraded KV4 or MQA ranking.

## Knowledge Inputs
- `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_v1.json`
- PR #719 folded attention tile/reducer PPA.
- PR #720 L1 FIFO/router PPA.
- Prior clustered schedule overhead result:
  `l2_decoder_attention_kv_clustered_schedule_overhead_llama7b_v1`.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-05-31T11:09:38Z
- note: Proceeded as an L2 measured-cost substitution before deeper L1 value-path closure.
