# Llama7B HBM-Closed On-Chip Schedule Closure

- source rows used: `48`
- generated rows: `103680`
- dominant resources: `{'tile_attention': 103680}`

## Best

| latency us | vs HBM source | resource | schedule | bank policy | endpoint q | bank q | router hop | packet | hbm cycles | shared service | exposed shared |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2138.84136 | 1.0 | tile_attention | static_wave | locality_first | 1024 | 1024 | 1 | 64 | 1301 | 225 | 225 |

## Best By Policy

| schedule | bank policy | latency us | vs source | resource | shared service | exposed shared |
|---|---|---:|---:|---|---:|---:|
| static_wave | locality_first | 2138.84136 | 1.0 | tile_attention | 225 | 225 |
| static_wave | age_based | 2138.84136 | 1.0 | tile_attention | 234 | 234 |
| staggered_wave | locality_first | 2138.84136 | 1.0 | tile_attention | 255 | 255 |
| staggered_wave | age_based | 2138.84136 | 1.0 | tile_attention | 264 | 264 |
| prefetch_overlap | locality_first | 2138.84136 | 1.0 | tile_attention | 240 | 0 |
| prefetch_overlap | age_based | 2138.84136 | 1.0 | tile_attention | 249 | 0 |
| static_wave | round_robin | 2139.032755 | 1.000089 | tile_attention | 242 | 242 |
| staggered_wave | round_robin | 2139.032755 | 1.000089 | tile_attention | 272 | 272 |
| prefetch_overlap | round_robin | 2139.032755 | 1.000089 | tile_attention | 257 | 0 |

## Best By Queue/Router

| endpoint q | bank q | router hop | packet | latency us | penalties | resource |
|---:|---:|---:|---:|---:|---|---|
| 1024 | 1024 | 1 | 64 | 2138.84136 | endpoint=0,bank=59 | tile_attention |
| 1024 | 1024 | 1 | 128 | 2138.84136 | endpoint=0,bank=25 | tile_attention |
| 1024 | 1024 | 1 | 256 | 2138.84136 | endpoint=0,bank=8 | tile_attention |
| 1024 | 2048 | 1 | 64 | 2138.84136 | endpoint=0,bank=50 | tile_attention |
| 1024 | 2048 | 1 | 128 | 2138.84136 | endpoint=0,bank=16 | tile_attention |
| 1024 | 2048 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 8192 | 1 | 64 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 8192 | 1 | 128 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 8192 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 32768 | 1 | 64 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 32768 | 1 | 128 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 1024 | 32768 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 1024 | 1 | 64 | 2138.84136 | endpoint=0,bank=59 | tile_attention |
| 2048 | 1024 | 1 | 128 | 2138.84136 | endpoint=0,bank=25 | tile_attention |
| 2048 | 1024 | 1 | 256 | 2138.84136 | endpoint=0,bank=8 | tile_attention |
| 2048 | 2048 | 1 | 64 | 2138.84136 | endpoint=0,bank=50 | tile_attention |
| 2048 | 2048 | 1 | 128 | 2138.84136 | endpoint=0,bank=16 | tile_attention |
| 2048 | 2048 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 8192 | 1 | 64 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 8192 | 1 | 128 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 8192 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 32768 | 1 | 64 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 32768 | 1 | 128 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 2048 | 32768 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |
| 8192 | 1024 | 1 | 64 | 2138.84136 | endpoint=0,bank=59 | tile_attention |
| 8192 | 1024 | 1 | 128 | 2138.84136 | endpoint=0,bank=25 | tile_attention |
| 8192 | 1024 | 1 | 256 | 2138.84136 | endpoint=0,bank=8 | tile_attention |
| 8192 | 2048 | 1 | 64 | 2138.84136 | endpoint=0,bank=50 | tile_attention |
| 8192 | 2048 | 1 | 128 | 2138.84136 | endpoint=0,bank=16 | tile_attention |
| 8192 | 2048 | 1 | 256 | 2138.84136 | endpoint=0,bank=0 | tile_attention |

## Assumptions

- HBM service cycles and controller parameters are inherited from the measured-HBM service source rows.
- This pass re-sweeps SRAM bank arbitration, endpoint queues, bank queues, packet payload, router hop latency, schedule staggering, and prefetch overlap.
- The model is still an analytic on-chip service simulator; it does not generate or prove full NoC RTL.
- Compute, measured SRAM capacity, local datapath PPA, endpoint/router/FIFO primitive PPA, and KV quality assumptions are inherited unchanged.
