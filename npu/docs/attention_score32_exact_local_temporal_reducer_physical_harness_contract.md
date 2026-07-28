# attention_score32_exact_local_temporal_reducer_physical_harness

This harness is a narrow-IO structural PPA wrapper around `gen_attention_score32_exact_local_temporal_reducer.py`.

- Inputs are fixed to `clk`, `rst_n`, `start`, and `seed`.
- Observable outputs are fixed to `done`, final command/head/max/sum/slice/last/value state, `source_fold`, and the harness counters.
- `producers` is fixed to `53` or `54`.
- `mode` is fixed to `reducer` or `source_only`.
- `waves` is fixed to `8`.
- Leaf traffic is generated from one shared held LFSR and one shared beat counter. Leaf-specific exact-partial fields are combinational and there are no per-leaf payload registers.
- All leaf valids form one atomic batch. Shared state advances only when every leaf handshakes, so every payload remains stable throughout reducer backpressure.
- `reducer` mode instantiates the existing merged local temporal reducer unchanged.
- Both modes retain the same full source fold. `source_only` accepts each batch atomically and additionally exposes direct source fields so the source fabric is not optimized away.
- The manifest must carry the caveats `structural_only` and `nonlinear_ppa_delta_vs_functional_reducer_measurement`.
- The harness never exposes an equivalence hash and must not be used as a functional replacement for the structured reducer probe.
