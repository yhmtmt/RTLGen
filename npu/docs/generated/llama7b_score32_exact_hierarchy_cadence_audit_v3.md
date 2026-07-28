# Score32 Exact Hierarchy Cadence Audit R3

- decision: `score32_986_cycle_arithmetic_not_sustained_by_corrected_group_command_mapping`
- supersedes only the erroneous R2 producer mapping/service conclusion
- historical arithmetic reference: `986` cycles
- corrected ideal-interface producer service: `1536` cycles
- excess: `+550` cycles

## Corrected Producer Mapping

- token blocks/tile: `128`
- token streams/producer: `2`
- GQA8 groups: `4`
- producer commands/datapath/wave: `4`
- p53 per group: `11` datapaths at 2 blocks/stream, `42` at 1
- p54 per group: `10` datapaths at 2 blocks/stream, `44` at 1
- rotated p53 extras across 4 groups: `44` datapaths get one `2`-block command, `9` get none
- rotated p54 extras across 4 groups: `40` datapaths get one `2`-block command, `14` get none
- worst-loaded per-wave schedule: `[2, 1, 1, 1]`

One dual-stream producer command covers one GQA8 head group for one tile wave and may aggregate either one or two token blocks per stream. R2's five-command one-block mapping is superseded.

## Corrected Producer Probe

- commands: `4`
- head bases: `[0, 8, 16, 24]`
- head dimension: `128`
- exact-partial output beats: `512`
- interface mode: `ideal`
- result stalls: `0`
- measured/reference ratio: `1.557809`

## Group-Major Reducer Schedule

- tile waves: `8`
- schedule: `process_one_fixed_gqa8_group_across_all_8_tile_waves_then_emit_finalize_before_next_head_base`
- safe interleave: `not_established`

## Non-Claims

- Do not treat the historical R2 five-command producer measurement as current evidence.
- Do not promote the 986-cycle tile service point from producer-only evidence.
- The 1536-cycle result is ideal-interface functional simulation for one tile wave on the worst-loaded datapath, not PPA or full producer-plus-NoC timing.
- No throughput revision is valid until the local reducer, group-major eight-wave persistence, and global c16 path are composed.
