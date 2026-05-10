# Decoder Output-Projection Producer Service

This proposal measures the planning-level service curve for the decoder final output-projection stage. The producer is not a full decoder; it is the stage that computes vocabulary-logit tiles from the current hidden vector and streams those tiles to the ranker.

The model derives integer producer II from tile MAC count and output-projection weight-memory service under a stage-serialized shared GEMM assumption.
