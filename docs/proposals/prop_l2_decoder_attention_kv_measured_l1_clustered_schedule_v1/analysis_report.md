# Analysis Report

## Candidate
- `proposal_id`: `prop_l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- `candidate_id`: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`

## Evaluations Consumed
- work item: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1`
- run key: `l2_decoder_attention_kv_measured_l1_clustered_schedule_v1_run_13be6b847e98c296`
- source commit: `0a1e86e0bce5672d52eb4b831971c0858bc84fab`
- result PR: #722
- merge commit: `30825fe1fd17bf9a2b84f00f7c90917cd38786f0`

## Sweep Summary
- generated rows: 3,194,880
- skipped area-budget rows: 0
- dominant tile resource counts:
  - tile attention: 2,183,552
  - cross-tile reduction: 854,784
  - command dispatch: 156,544

## Best Point
- latency: 15,133.019664 us
- die area: 1200 mm2
- SRAM fraction: 0.4
- logic fraction: 0.2
- local SRAM fraction: 0.1
- bank count: 16
- NoC bandwidth: 8192 bytes/cycle
- NoC hops: 1
- reduction: `cluster_tree`
- measured L1 profile: `hd64_kv4_p8_ppc2_noc128`
- compute: `nm64_flat`
- compute replicas: 265
- clusters: 8
- MAC/cycle: 16,960
- clock: 6.6331 ns
- measured L1 overhead area: 440,292.3894 um2
- logic area used: 239,503,417.3894 um2

## Best By Die
| die mm2 | latency us | compute | replicas | clusters | L1 profile | dominant |
|---:|---:|---|---:|---:|---|---|
| 200 | 90,764.368771 | nm64_flat | 44 | 4 | hd64_kv4_p8_ppc2_noc128 | tile_attention |
| 400 | 45,387.384736 | nm64_flat | 88 | 8 | hd64_kv4_p8_ppc2_noc128 | tile_attention |
| 800 | 22,669.494819 | nm64_flat | 177 | 1 | hd64_kv4_p8_ppc2_noc128 | cross_tile_reduction |
| 1200 | 15,133.019664 | nm64_flat | 265 | 8 | hd64_kv4_p8_ppc2_noc128 | tile_attention |

## Result
The measured L1 local-cost charge does not overturn the broad frontier. The
winner still uses the largest measured compute block family and the smallest
local L1 profile. Measured local area is small relative to the 1200 mm2,
20%-logic budget in the best point, so the current sweep is still dominated by
compute throughput and reduction scheduling rather than local FIFO/router area.

## Caveats
- The measured L1 profile is a partial local datapath proxy.
- The full softmax-weighted value datapath is not yet closed in RTL/PPA.
- NoC/SRAM arbitration is still analytic.
- The old L2 baseline record was absent from the rebuilt DB, so this run gated
  only on the two merged L1 source items and kept the old L2 result as a paired
  comparison reference.

## Recommendation
Iterate. The next architecture job should close the full local attention value
datapath and then replace the abstract NoC/SRAM service model with a more
explicit cluster-memory network model.
