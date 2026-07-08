# Score32 HBM Controller Replay

- decision: `score32_hbm_controller_replay_compute_dominant`
- best latency us: `12814.257853`
- best throughput token/s: `78.038073798`
- best latency total energy mJ/token: `467.189908559`
- best hbm-dominant: `False`

## Best Replay Row

| ch | ch B/cyc | burst | row span | miss penalty | miss count | overhead | out | gap | row hit | eff | service cyc | added us | latency us | throughput |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 1024.0 | 1024 | 16 | 8 | 64 | 2 | 4 | 0 | 0.95 | 0.75 | 1136 | 0.0 | 12814.257853 | 78.038073798 |

## Top 10

| rank | latency us | total energy | throughput | channels | out | burst | row span | misses | service cyc |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 4 | 1024 | 16 | 64 | 1136 |
| 2 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 4 | 1024 | 16 | 64 | 1136 |
| 3 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 8 | 1024 | 16 | 64 | 1136 |
| 4 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 8 | 1024 | 16 | 64 | 1136 |
| 5 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 16 | 1024 | 16 | 64 | 1136 |
| 6 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 16 | 1024 | 16 | 64 | 1136 |
| 7 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 32 | 1024 | 16 | 64 | 1136 |
| 8 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 32 | 1024 | 16 | 64 | 1136 |
| 9 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 4 | 1024 | 16 | 64 | 1264 |
| 10 | 12814.257853 | 467.189908559 | 78.038073798 | 4 | 4 | 1024 | 16 | 64 | 1264 |

## Assumptions

- Replay builds a deterministic burst stream with round-robin channel interleave.
- Each channel has row-window state with misses determined by row_span_bursts and adjusted to hit_rate.
- Per-request cycles include burst transfer payload, request overhead, row-miss penalty, and scheduler gap.
- Outstanding requests are enforced as a global in-flight limit.
- Replay latency is added to the schedule-wrapper recost source latency by mapping replay-cycle delta vs source HBM/service cycles.
- HBM energy is inherited from the score32 HBM closure; compute energy is rebuilt from physical wrapper compute power.
