# Decoder Producer/Ranker/Memory Integration Plan

- model: `decoder_producer_ranker_memory_integration_plan_v1`
- measured_mac_lanes_per_cycle: `16`
- physical_anchor: `nm16 3_3_place_gp cp=6.10444708970485ns`
- next_target: `r64_k1_nm16_ready_valid_equivalence`

## Integration Rows

| shape | W | top_k | model MAC/cyc | ranker_us | nm16_model_us | nm16_physical_us | model limiter | physical limiter | clusters |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|
| gpt2_medium_proxy | 64 | 1 | 8192 | 6728.322951 | 3219.464 | 19653.047645 | ranker | producer_mac_limited | 512 |
| gpt2_small | 64 | 1 | 8192 | 5046.275694 | 2414.598 | 14739.785734 | ranker | producer_mac_limited | 512 |

## Recommendation

- add producer-to-ranker LogitTileStream/CandidateStream ready-valid equivalence harness
- measure a macro-style r64/k1 wrapper with one-entry skid buffers and no exposed scalar logit pins
- only then scale producer MAC parallelism or shared-memory/NoC arbitration

## Assumptions

- Producer num_modules and producer_lanes are different axes: num_modules is measured FP16 MAC parallelism, producer_lanes is logit tile width.
- The nm16 physical anchor proves bounded feasibility for the current generated producer wrapper, not an 8192-MAC output-projection array.
- Latency rows are recalculated with the same weight-memory model but with measured nm16 MAC lanes to expose the physical/analytical gap.
- Ready/valid stream equivalence must be validated before integrated RTL PPA is used in rankings.
