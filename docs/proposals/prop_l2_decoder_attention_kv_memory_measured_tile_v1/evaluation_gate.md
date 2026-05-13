# Evaluation Gate

- Run `l2_decoder_attention_kv_memory_measured_tile_v1`.
- Confirm the JSON report includes `measured_attention_kv_tile_frontier`.
- Confirm the measured frontier records six best design points and twelve raw
  accepted rows from the merged Layer 1 metrics.
- Confirm the markdown report includes the measured tile table.
- Treat the result as a calibrated analytical report, not integrated RTL PPA.
- Use the result to choose whether the next job should be producer/memory/NoC
  coupled attention work.
