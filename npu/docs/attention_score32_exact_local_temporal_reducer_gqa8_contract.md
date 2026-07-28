# Score32 Exact Local Temporal Reducer GQA8 Contract

This block is the GQA8-compatible local temporal reducer for the exact score32
partial path. It is intentionally separate from the historical
`gen_attention_score32_exact_local_temporal_reducer.py` evidence path, which
remains the older 16-bank single-head reducer.

## Scope

- `53`- or `54`-way staged exact-partial local reduction
- `8` query heads per command group
- `16` value slices per head
- `8` persistent local waves per command group
- exact-partial output only (`328` payload bits per beat)
- `128` emitted beats after wave `8` (`8 heads x 16 slices`)

The reducer reuses the existing staged local reducer and the existing exact
online-state merge stage. The new behavior is in the temporal banking and the
group-validation contract.

## Input Group Contract

- One command group carries one explicit `head_base` represented directly by
  the incoming `head_id` metadata.
- The first accepted local-root beat for a command group must be:
  - `slice=0`
  - `last=0`
  - `head_id=head_base`
  - `head_base` aligned to `8`
- The accepted local-root stream for each wave is serialized in producer order:
  `head0 slice0..15`, then `head1 slice0..15`, through `head7 slice0..15`.
- Every accepted beat must preserve exact `command_id`, `head_id`, `slice`,
  `last`, `global_max`, `exp_sum`, and `8 x S41` numerator metadata.
- `last=1` still appears on slice `15` of every head. This marker does not
  advance the wave by itself.

## Wave-Advance Contract

- Temporal state is banked across `128` entries: `8 heads x 16 slices`.
- Wave advance is legal only after the validated terminal beat
  `head_base + 7, slice 15, last=1`.
- The reducer therefore consumes `128` local roots per wave, not `16`.
- After the eighth validated wave, the reducer emits the full `128`-beat
  aggregate in the same head-major, slice-minor order.

## Probe Evidence

Recorded on July 28, 2026 with:

- `python npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py --config runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_p53_w8/config.json --out /tmp/score32_exact_local_temporal_reducer_gqa8_p53.json`
- `python npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py --config runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_p54_w8/config.json --out /tmp/score32_exact_local_temporal_reducer_gqa8_p54.json`
- `python npu/eval/probe_attention_score32_exact_local_temporal_reducer_gqa8.py --config runs/designs/npu_blocks/attention_score32_exact_local_temporal_reducer_gqa8_p53_w8/config.json --stress-interfaces --out /tmp/score32_exact_local_temporal_reducer_gqa8_p53_stress.json`

Checked-in two-group point:

- head groups: `2`
- command head_bases: `[0, 8]`
- producer-compatible input ordering: pass
- exact-partial output beats: `256`
- local roots: `2048`
- temporal merges: `1792`
- completed groups: `2`
- exact beat and metadata equivalence: pass

Per-group counts:

- local roots: `1024`
- temporal merges: `896`
- outputs: `128`

Both the ideal and stressed probes compare every emitted beat against a
structured Python reference. The stressed probe keeps the same exact
beat-for-beat comparison under input skew and output backpressure.

## Remaining Abstractions

- `producer_to_local_reducer_structural_fan_in_open`
- `noc_sram_ppa_open`
- `global_c16_exact_reduction_open`

No PPA claim, NoC closure claim, SRAM banking closure claim, or global c16
integration claim is made here.
