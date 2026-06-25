# Llama7B Mixed/Int8 Score32 Generation Quality

This proposal adds a bounded generation/NLL quality gate after the score-margin audit. It checks whether the score32 mixed/int8 candidate preserves reference-token likelihood and greedy generated tokens before any new PPA recost is launched.

The job is evidence-only and does not run physical design.
