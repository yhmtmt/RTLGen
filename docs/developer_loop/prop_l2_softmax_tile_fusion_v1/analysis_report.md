# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_softmax_tile_fusion_v1`
- `candidate_id`: `cand_softmax_tail_fused_output_v1_r1`

## Evaluations Consumed
- work item id: `l2_prop_l2_softmax_tile_fusion_v1_20260316051355`
- run key: `l2_prop_l2_softmax_tile_fusion_v1_20260316051355_run_b992c4d7a804af22`
- source commit: `f029b6f1a712844a663de7892bbb07f98c340f85`
- review PR: `#36`

## Baseline Comparison
- baseline:
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_submit_v1/`
- older reference baseline:
  `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_num_modules_v1/`
- key deltas:
  - the proposal run reused the same `softmaxcmp` physical design points as the
    accepted dedicated-softmax baseline
  - the mapper changed only the terminal routing rule to allow
    `SOFTMAX -> Y_DRAM` and remove trailing `dma_y`
  - the winning point remained `fp16_nm1_softmax_r4` with the same reported
    best latency, energy, area, power, and flow metrics as the accepted
    dedicated-softmax baseline
  - `fp16_nm2_softmax_r4` improved slightly under fused output, but still lost
    to `fp16_nm1_softmax_r4`

## Result
- result: `mixed`
- confidence: `medium`
- interpretation:
  the fused-output mapper path is functionally valid and removes one terminal
  DMA hop, but this evaluation did not show a proposal-level win over the
  existing dedicated-softmax baseline

## Failures and Caveats
- no flow failures were reported in the remote campaign
- no numerical-quality regression was reported by the quality gate
- mapper limitations remain material:
  - `fp16_nm2_softmax_r4` was evaluated with one heuristic row-split schedule
    rather than a bounded schedule search
  - the current result is therefore not strong enough to conclude that the
    multi-module architecture itself is inferior
  - the proposal answered the direct-output legality question, but not the
    broader mapper-optimality question for multi-module softmax-tail execution

## Recommendation
- `iterate`
- reason:
  keep the architecture result as valid negative evidence for the current
  heuristic, but open a mapper-focused follow-on item before making stronger
  architecture conclusions
- follow-on:
  `docs/development_items/items/item_l2_mapper_memory_aware_split_v1.md`
