# Shared-SRAM Adapter RTL/Perf Frontier

- passed: `true`
- common_clock_period_ns: `2.0`
- precision: `exact_lossless_no_precision_change`

| Design | Cycles | Latency (ns) | Area (um2) | Power (mW) | Energy/group (pJ) |
|---|---:|---:|---:|---:|---:|
| attention_shared_sram_read_group_adapter_w256_s1 | 682 | 1364.000 | 5482.53 | 0.002860 | 0.060954 |
| attention_shared_sram_read_group_adapter_w256_s2 | 346 | 692.000 | 6729.27 | 0.003610 | 0.039033 |
| attention_shared_sram_read_group_adapter_w512_s1 | 409 | 818.000 | 5458.59 | 0.002840 | 0.036299 |
| attention_shared_sram_read_group_adapter_w512_s2 | 208 | 416.000 | 6754.54 | 0.003500 | 0.022750 |

- adapter group-service throughput winner: `attention_shared_sram_read_group_adapter_w512_s2`
- adapter vectorless total-energy proxy winner: `attention_shared_sram_read_group_adapter_w512_s2`
- area winner: `attention_shared_sram_read_group_adapter_w512_s1`
- SRAM bitcell area is excluded; this report closes adapter logic and scheduling only.
