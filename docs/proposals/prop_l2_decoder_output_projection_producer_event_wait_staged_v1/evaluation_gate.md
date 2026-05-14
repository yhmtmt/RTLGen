# Evaluation Gate

Dispatch `l2_decoder_output_projection_producer_event_wait_staged_v1` after the staged EVENT_WAIT RTL generator change is merged.

The gate passes if the evaluator runs the existing SOFTMAX/EVENT ablation on the merged commit and records whether the prior EVENT_WAIT timeout moved to a bounded synth result.
