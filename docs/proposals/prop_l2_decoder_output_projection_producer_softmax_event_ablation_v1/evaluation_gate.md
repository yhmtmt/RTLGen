# Evaluation Gate

Dispatch `l2_decoder_output_projection_producer_softmax_event_ablation_v1` after `l2_decoder_output_projection_producer_cq_ablation_v1` is merged and finalized.

The gate passes if each SOFTMAX/EVENT subpath variant records either a bounded synth result or a clear generation/synthesis failure classification.
