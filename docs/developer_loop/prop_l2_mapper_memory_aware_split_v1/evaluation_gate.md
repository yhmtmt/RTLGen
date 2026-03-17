# Evaluation Gate

- status: approved
- approved_by: `user`
- approved_utc: `2026-03-17T07:00:00Z`
- allowed_evaluations:
  - `l2_campaign`: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with objective focus `balanced`
  - `l2_campaign`: `runs/campaigns/npu/e2e_eval_onnx_imported_softmax_tail_softmax_macro_fused_output_v1/campaign.json` with objective focus `latency`
- note: `quality_gate.md` passed and the implementation is limited to mapper
  schedule selection plus reporting. Proceed with the same fused-output
  softmaxcmp campaign so the new source commit can be compared directly against
  the prior accepted baseline and prior iterate result.
