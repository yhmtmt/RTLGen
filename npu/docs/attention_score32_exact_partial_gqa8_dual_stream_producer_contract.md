# Score32 Exact Partial GQA8 Dual-Stream Producer Contract

This block is a new functional local producer slice for the 128-MAC exact
partial path. It is intentionally separate from the historical
`attention_score32_exact_partial_producer_tree` evidence path.

## Scope

- two token streams
- eight query-head lanes per stream (`GQA8`)
- shared score-K broadcast within each stream
- explicit `head_base + lane` head IDs
- pairwise exact-partial merge across the two streams
- exact-partial output only (`328` payload bits, `419` link bits)

The structural score rate is `2 streams x 8 heads x 8 token lanes = 128`
MAC/cycle.

Each stream is built from the existing real
`attention_decode_score_multivalue_gqa_group` extended to
`result_mode="exact_partial"`. Corresponding stream outputs are merged with the
existing exact-partial merge stage. The functional RTL preserves the full
partial state on every beat: `global_max`, `exp_sum`, `slice`, `last`, and
`8 x S41` numerators.

## Local-Wave Storage Contract

- `max_blocks=8` is the intended local producer limit.
- A `1024`-token tile is partitioned into `128` token blocks and distributed
  across `53/54` datapaths and `2` token streams, so each local stream sees at
  most `2` token blocks per wave.
- The checked-in smoke probe uses `1` command, `2` blocks per stream, and
  `head_dim=3`.
- This producer emits one wave at a time. Local `53/54`-way aggregation and
  persistent temporal accumulation across `8` waves remain outside this slice.

## Remaining Abstractions

- `53or54_way_global_cluster_aggregation_open`
- `8_wave_persistent_state_open`
- `noc_sram_ppa_open`

No global reduction closure, NoC closure, SRAM banking closure, or PPA closure
is claimed here.

## Value-Memory Contract

- The implemented interface is per-stream GQA-coalesced value service, reused
  from the GQA group generator.
- Shared K/V request coalescing is functional within each stream.
- No claim is made about full global K/V memory closure beyond the local stream
  interface.

## Probe Evidence

Recorded on July 28, 2026 with:

- `python npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py --config runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config.json --json`
- `python npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py --config runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config_heads32_native.json --json`
- `python npu/eval/probe_attention_score32_exact_partial_gqa8_dual_stream_producer.py --config runs/designs/npu_blocks/attention_score32_exact_partial_gqa8_dual_stream_producer_b8/config_llama_wave.json --json`

Checked-in smoke point:

- heads: `8`
- command groups: `1`
- exact-partial output beats: `128`
- integrated drain cycles: `438`
- command accepts/completions: `1 / 1`
- stream accepts/completions: `[1, 1] / [1, 1]`
- merge completions: `128`
- result stall cycles under probe backpressure: `64`

Full native point:

- heads: `32`
- command groups: `4`
- blocks per stream: `2`
- head_dim: `3`
- exact-partial output beats: `512`
- integrated drain cycles: `1736`
- command accepts/completions: `4 / 4`
- stream accepts/completions: `[4, 4] / [4, 4]`
- merge completions: `512`
- result stall cycles under probe backpressure: `255`

Llama-wave functional service point:

- heads: `32`
- command groups: `5`
- command head_bases: `[0, 8, 16, 24, 0]`
- blocks per stream: `1`
- head_dim: `128`
- exact-partial output beats: `640`
- ideal command/input/value-request/output interfaces
- minimum modeled value-response latency
- integrated drain cycles: `1681`
- compared directly to `986` cycles: `+695`
- command accepts/completions: `5 / 5`
- stream accepts/completions: `[5, 5] / [5, 5]`
- merge completions: `640`
- result stall cycles: `0`
- exact beat equivalence: pass
- compared directly to `986` cycles as functional service evidence only
- this is not a frontier revision

Both probes compare every emitted beat against a structured Python exact-partial
reference. No hash reduction is used in the functional comparison path.
