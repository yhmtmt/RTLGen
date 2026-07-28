# Score32 Exact Hierarchy Cadence Audit R2

- decision: `score32_986_cycle_arithmetic_not_sustained_by_functional_exact_producer`
- historical arithmetic reference: `986` cycles
- functional ideal-interface service: `1681` cycles
- excess: `+695` cycles

## Corrected Mapping

- token blocks/tile: `128`
- paired token blocks: `64`
- GQA8 groups: `4`
- paired GQA jobs/wave: `256`
- 53 datapaths: `44` carry 5 jobs, `9` carry 4
- 54 datapaths: `40` carry 5 jobs, `14` carry 4

A producer command covers one paired token block for one GQA8 head group. The prior stream-level 1/2-block assignment did not account for all four GQA groups and is superseded by this mapping.

## Functional Evidence

- commands on the worst-loaded datapath: `5`
- head bases: `[0, 8, 16, 24, 0]`
- head dimension: `128`
- exact-partial output beats: `640`
- interface mode: `ideal`
- result stalls: `0`
- measured/reference ratio: `1.704868`

The functional producer does not sustain the 986-cycle arithmetic point even with ideal external interfaces. The current frontier must remain unpromoted.

## Next Measurement

- functional 53/54-way local exact reduction
- persistent local exact state across eight waves
- one global c16 exact reduction after local aggregation

## Non-Claims

- Do not promote the 986-cycle tile service point.
- The 1681-cycle result is ideal-interface functional simulation, not PPA or full producer-plus-NoC timing.
- No throughput revision is valid until the local reducer, persistent eight-wave state, and global c16 path are composed.
