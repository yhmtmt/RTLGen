# Decoder Logit-Rank Streaming Hierarchy

This proposal records the documentation/spec slice and first-order estimator
for composing measured logit-rank tiles into a full-vocabulary decoder
reduction path.

Artifacts:

- `proposal.json`: proposal metadata and review scope
- `evaluation_requests.json`: frontier-detail review request
- `design_brief.md`: problem, hypothesis, and scope
- `evaluation_gate.md`: pending review gate
- `npu/docs/decoder_logit_rank_streaming_hierarchy.md`: architecture spec
- `npu/eval/estimate_llm_decoder_logit_rank_streaming_hierarchy.py`: estimator
  entry point

No RTL or physical implementation changes are part of this slice.
