# Evaluation Gate

- status: approved_after_merge
- approved_by: developer_agent
- approved_utc: 2026-05-02T05:45:00Z
- allowed_evaluations:
  - `l1_decoder_q12_pwl_softmax_datapath_v1`: L1 measurement-only sweep for the q12 PWL-exp row-wise softmax datapath with exact normalization.
- note: The evaluator must run this from a commit containing `softmax_rowwise` `impl=pwl_exp` support.
