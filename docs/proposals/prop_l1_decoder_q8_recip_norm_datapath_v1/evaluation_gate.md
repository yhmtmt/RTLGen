# Evaluation Gate

- status: approved_after_merge
- approved_by: developer_agent
- approved_utc: 2026-04-29T00:00:00Z
- allowed_evaluations:
  - `l1_decoder_q8_recip_norm_datapath_v1`: L1 measurement-only sweep for q10/q12/q14/q16 integrated reciprocal-normalization softmax blocks.
- note: The evaluator must run this from a commit containing `normalization_mode=reciprocal_quantized` support.
