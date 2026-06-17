# Softmax-Recip Subtile Pipeline Schedule

This proposal evaluates a sub-tile QK/softmax/V pipeline schedule on top of the
merged softmax-recip HBM-closed Llama7B attention frontier.

Best observed result:
- latency: `1575.373891 us`
- speedup versus HBM-closed source: `1.357672x`
- dominant resource: `pipeline_attention`
- selected schedule: `subtile_count=8`, `subtile_buffer_count=4`,
  `prefetch_distance=3`, `normalize_strategy=online_correction`,
  `compute_mode=dual_mac`
- stream buffer: `532608 B` required versus `614656 B` available

The result moves the bottleneck from unpipelined `tile_attention` to
`pipeline_attention`, while HBM exposure remains below the pipeline stage.
