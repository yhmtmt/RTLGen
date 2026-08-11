# Design Brief

- Consume only `l2_decoder_attention_score32_noc_phase2_schedule_llama7b_v1_r1`.
- Consume only the exact `p5/w256/vc4/d4` timing-feasible router promotion.
- Rerun all eight waves and 128 tiles at the primitive critical-path clock and
  at `max(1 ns, critical_path_ns)`.
- Recompute release cycles and contention; never scale the old absolute 1 ns
  cycle timeline.
- Treat the primitive-clock case as diagnostic when it is faster than 1 ns and
  the no-faster-than-source case as the conservative schedule bound.
