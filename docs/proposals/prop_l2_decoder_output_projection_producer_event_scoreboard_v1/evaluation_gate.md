# Evaluation Gate

Dispatch `l2_decoder_output_projection_producer_event_scoreboard_v1` after the bounded EVENT scoreboard RTL generator change is merged.

The gate passes if the evaluator reruns the SOFTMAX/EVENT ablation on the merged commit and records whether the prior EVENT_WAIT timeout moved to a bounded synth result.
