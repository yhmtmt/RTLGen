# Score32 Exact Partial GQA8 Dual-Stream Producer Worst-Loaded Wave Probe

- config: `runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config_llama_wave_worst4_group_major.json`
- date: `2026-07-28`
- decision: `score32_exact_partial_dual_stream_gqa8_pass`
- heads: `32`
- commands: `4`
- block counts per stream: `[2, 1, 1, 1]`
- head bases: `[0, 8, 16, 24]`
- head_dim: `128`
- exact-partial output beats: `512`
- interface mode: `ideal`
- integrated drain cycles: `1536`
- delta vs 986 cycles: `550`
- command accepts/completions: `4 / 4`
- stream accepts/completions: `[4, 4] / [4, 4]`
- merge completions: `512`
- result stall cycles: `0`
- protocol error: `False`
- exact structured equivalence: pass
- committed equivalence evidence: expected/observed beat counts and SHA-256 digests; full payload rows omitted

This is the corrected worst-loaded per-wave producer schedule for one datapath: four group commands with block counts `[2, 1, 1, 1]` under ideal interfaces. It does not include the group-major eight-wave local reducer or the final global c16 exact reduction.
