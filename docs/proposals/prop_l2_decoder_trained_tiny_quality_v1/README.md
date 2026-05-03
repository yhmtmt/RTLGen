# Decoder Trained Tiny Quality Gate

This proposal records the first trained-weight tiny decoder quality check for
the bf16/PWL reciprocal normalization frontier.

Primary files:

- `proposal.json`: scope, hypothesis, dependencies, and required evaluation
- `design_brief.md`: rationale for using a trained tiny GPT-2-family smoke
- `quality_gate.md`: evaluator acceptance criteria
- `evaluation_requests.json`: dispatched L2 work item metadata

The evaluation is pending on `l2_decoder_trained_tiny_quality_v1`. A pass here
only authorizes a larger trained-model confirmation; it does not prove behavior
on distilgpt2, GPT-2, or larger arrays.
