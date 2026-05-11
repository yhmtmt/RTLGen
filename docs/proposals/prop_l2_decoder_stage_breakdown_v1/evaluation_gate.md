# Evaluation Gate

- Run `l2_decoder_stage_breakdown_v1`.
- Confirm the report includes attention, MLP, output projection, and ranker stage shares.
- Confirm both `streaming_weights` and `resident_weights` cases are reported.
- Treat the result as an analytical dominance map, not measured RTL.
- Use the result to choose the next RTL target only after checking whether the conclusion is stable across sequence length and memory bandwidth.
