# Llama7B Attention NoC Profile

## Traffic Quantities

| quantity | bytes |
|---|---:|
| full_tile_kv_bytes | 524288 |
| shared_tile_payload_bytes | 230713 |
| partial_reduction_payload_bytes | 8320 |
| cross_tile_reduction_payload_bytes | 66560 |
| kv_write_payload_bytes | 1024 |

## Best Shared-Tile Service Rows

| flit | raw B/cyc | hops | vc | arb | eff agg B/cyc | eff cluster B/cyc | tile cycles | reduction cycles |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 128 | 32768.0 | 1 | 4 | 0.85 | 27852.8 | 3481.6 | 69 | 5 |
| 256 | 32768.0 | 1 | 4 | 0.85 | 27852.8 | 3481.6 | 69 | 5 |
| 128 | 32768.0 | 1 | 2 | 0.85 | 25067.52 | 3133.44 | 76 | 5 |
| 256 | 32768.0 | 1 | 2 | 0.85 | 25067.52 | 3133.44 | 76 | 5 |
| 128 | 32768.0 | 1 | 1 | 0.85 | 23674.88 | 2959.36 | 80 | 5 |
| 256 | 32768.0 | 1 | 1 | 0.85 | 23674.88 | 2959.36 | 80 | 5 |
| 128 | 32768.0 | 1 | 4 | 0.7 | 22937.6 | 2867.2 | 83 | 5 |
| 256 | 32768.0 | 1 | 4 | 0.7 | 22937.6 | 2867.2 | 83 | 5 |
| 128 | 32768.0 | 1 | 2 | 0.7 | 20643.84 | 2580.48 | 92 | 6 |
| 256 | 32768.0 | 1 | 2 | 0.7 | 20643.84 | 2580.48 | 92 | 6 |
| 128 | 32768.0 | 1 | 1 | 0.7 | 19496.96 | 2437.12 | 97 | 6 |
| 256 | 32768.0 | 1 | 1 | 0.7 | 19496.96 | 2437.12 | 97 | 6 |

## Measured Primitive Inputs

### 128-bit flits
- fifo: area `13882.730625` um2, clock `0.2898` ns, power `0.00863` mW
- router: area `3724.050625` um2, clock `0.2411` ns, power `0.00171` mW
### 256-bit flits
- fifo: area `11779.846225` um2, clock `0.29` ns, power `0.00869` mW
- router: area `3299.3536` um2, clock `0.2401` ns, power `0.00171` mW

## Notes

- Rows are service bounds for selected traffic; they close the hidden NoC-efficiency knobs but do not replace a full routed NoC implementation.
