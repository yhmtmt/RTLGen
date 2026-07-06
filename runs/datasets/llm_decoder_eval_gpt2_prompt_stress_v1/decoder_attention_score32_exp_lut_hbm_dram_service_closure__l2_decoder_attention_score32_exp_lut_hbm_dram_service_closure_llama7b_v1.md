# Score32 exp-LUT HBM/DRAM Service Closure

- decision: `score32_exp_lut_hbm_dram_service_closure_hbm_sensitive`
- best latency us: `12532.357427`
- best throughput token/s: `79.793447149`
- best latency HBM energy mJ/token: `134.280615241`
- best latency total energy mJ/token: `494.831007886`
- HBM-dominant rows: `35413` / `43740`

## Best Latency

| latency us | token/s | HBM energy mJ | total energy mJ | hbm share | efficiency | channels | ch B/cyc | burst | outstanding | row hit | sched | service cyc |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12532.357427 | 79.793447149 | 134.280615241 | 494.831007886 | 0.984420776 | 1.0 | 4 | 256 | 1024 | 32 | 0.9 | 0.9 | 1217 |

## Assumptions

- The score32 exp-LUT compute/datapath, command control, SRAM envelope, and precision evidence are inherited from merged score32 results.
- HBM service is modeled with channel count, per-channel bytes/cycle, burst size, outstanding window, row-hit rate, and scheduler efficiency.
- HBM energy uses the existing command-calibrated pJ parameters from the design registry calibration chain.
- This is not a cycle-accurate HBM/DRAM controller RTL simulation or vendor current signoff.
