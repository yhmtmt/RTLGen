# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_kv_all_measured_l1_clustered_schedule_v1`
- `title`: `All-measured Llama7B attention L2 clustered schedule`

## Problem
The current Llama7B long-context attention frontier still mixes measured local
datapath costs with analytic service terms. Before exploring larger die-size and
cluster spaces, the local L1 attention stack needs a stable all-measured
baseline that includes compute, full-value tile datapaths, exact softmax weight
generation, and local NoC anchors.

## Hypothesis
If the exact softmax generator and local FIFO/router costs are small compared
with compute and memory service, the measured frontier should remain close to
the prior full-value clustered result. A shift would indicate that one of the
previously abstracted local blocks was materially affecting the schedule.

## Evaluation Scope
- direct comparison set: `fp16_nm1` and `fp16_nm2`, each ranked in
  `flat_nomacro` and `hier_macro` modes.
- evaluation mode: `broad_ranking`.
- dependency order: uses merged measured compute PPA, full-value L1 attention
  tile costs, exact-int softmax generator promotion, and SRAM/NoC profile
  references.
- excluded first-stage comparisons: new SRAM macros, global NoC arbitration
  RTL, quality-changing KV approximations, and wider `nm`/cluster sweeps.
- follow-on broad sweep: expand parallelism and replace remaining analytic
  SRAM/global-NoC service terms with physically constrained blocks.

## Knowledge Inputs
- `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_full_value_v1.json`
- `runs/campaigns/npu/l1_measured_costs/llama7b_attention_local_costs_all_measured_v1.json`
- `control_plane/shadow_exports/l1_promotions/l1_decoder_attention_softmax_weight_generator_v1_r2.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_noc_profile__l2_decoder_attention_noc_profile_v1.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json`

## Candidate Direction
Record the all-measured local L1 cost stack as the current Llama7B attention
baseline, while keeping SRAM/global-NoC assumptions visible for the next
frontier expansion.

## Direction Gate
- status: approved
- approved_by: developer_agent
- approved_utc: 2026-06-03T03:17:10Z
- note: Retry was required after the r2 estimator retained too many rows and was
  terminated by the evaluator.

