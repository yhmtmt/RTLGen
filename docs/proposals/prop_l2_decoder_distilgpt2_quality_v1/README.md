# Decoder distilgpt2 Quality Gate

This proposal records the first larger trained-checkpoint confirmation for the
bf16/PWL reciprocal normalization frontier.

Primary files:

- `proposal.json`: scope, hypothesis, dependencies, and required evaluation
- `design_brief.md`: rationale for using distilgpt2 after trained tiny recovery
- `quality_gate.md`: evaluator acceptance criteria
- `evaluation_gate.md`: approved evaluation list

The evaluation should be dispatched as `l2_decoder_distilgpt2_quality_v1` after
the task-generator support is merged.
