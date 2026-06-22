# Design Brief

## Proposal
- `proposal_id`: `prop_l2_decoder_attention_dense_gemm_v3_measured_compute_closure_llama7b_v1`
- `title`: `Llama7B measured compute closure with dense GEMM V3 metrics`

## Problem
PR #981 showed that abstract compute assumptions can invalidate the Llama7B frontier.
The V3 dense-GEMM tile merge now adds a larger, higher-confidence measured dense-tile
anchor, so the L2 frontier must be reranked before the next architecture step.

## Hypothesis
Replacing the PR #981 measured-compute source rows with merged V3 dense-GEMM replica data will either
reconfirm the current family or force a new selection if 524288 MAC/cycle remains
infeasible under the measured macro density and area budget.

## Evaluation Scope
- direct comparison set:
  - PR #981 measured-compute frontier vs. the reranked V3-dense-GEMM rerank
  - source-backed HBM command-calibrated service terms
  - SRAM profile terms
- evaluation mode:
  - `frontier_detail` rerank only
- dependency order:
  - `l1_npu_dense_gemm_tile_scaling_v3` must be merged before rerank
  - then `l2_decoder_attention_measured_compute_energy_closure_llama7b_v1` and
    `l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1` are required inputs
- excluded first-stage comparisons:
  - no new PPA/OpenROAD sweeps, no quality/QAT exploration
  - no new HBM, SRAM, or NoC physical model changes
- follow-on broad sweep:
  - if the dense-V3 rerank changes family, keep it as baseline for integrated compute or SRAM/NoC closure jobs
  - if unchanged, proceed with residual-service sensitivity jobs

## Knowledge Inputs
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_measured_compute_energy_closure__l2_decoder_attention_measured_compute_energy_closure_llama7b_v1.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_hbm_command_calibrated_service__l2_decoder_attention_hbm_command_calibrated_service_llama7b_v1.json`
- `runs/datasets/llm_decoder_eval_gpt2_prompt_stress_v1/decoder_attention_sram_profile__l2_decoder_attention_sram_profile_v1.json`
- `item:l1_npu_dense_gemm_tile_scaling_v3`

## Candidate Direction
Adopt the V3-dense-compute frontier if it is feasible under the current HBM/SRAM accounting,
otherwise keep the PR #981 corrected baseline and continue to residual-service closure work.

## Direction Gate
- status: blocked_until_l1_v3_merged
- note: Wait for `l1_npu_dense_gemm_tile_scaling_v3` merge and dispatch to
  `eval-daemon-b7c2d9c80c1c`.
