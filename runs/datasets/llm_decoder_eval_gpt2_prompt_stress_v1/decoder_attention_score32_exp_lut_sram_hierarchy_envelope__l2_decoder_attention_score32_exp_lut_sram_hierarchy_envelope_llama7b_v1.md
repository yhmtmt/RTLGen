# Score32 exp-LUT SRAM Hierarchy Envelope

- decision: `score32_exp_lut_sram_hierarchy_envelope_stable`
- source score32 latency us: `12519.342352`
- source hbm share: `0.983398438`
- nominal efficiency: `0.75`
- nominal shared MiB: `47.8125`
- nominal hbm share: `0.988327026`
- conservative efficiency: `0.55`
- conservative shared MiB: `35.046875`
- conservative hbm share delta: `0.008045196`

## Sweep

| efficiency | shared MiB | hbm share | projected latency us | shared envelope um2 | fits |
|---:|---:|---:|---:|---:|---|
| 1.0 | 63.8125 | 0.984420776 | 12532.357427 | 225752530.670304 | True |
| 0.85 | 54.28125 | 0.986747742 | 12561.981305 | 225727744.261661 | True |
| 0.75 | 47.8125 | 0.988327026 | 12582.086691 | 225688539.122645 | True |
| 0.65 | 41.515625 | 0.989864349 | 12601.657876 | 225666992.975855 | True |
| 0.55 | 35.046875 | 0.991443634 | 12621.763263 | 225602485.734324 | True |

## Assumptions

- SRAM macro placement efficiency is modeled as macro_area/envelope_area and swept explicitly.
- Tile-local SRAM area and endpoint/router/FIFO area are reserved before packing shared SRAM.
- Shared SRAM capacity uses the existing CACTI macro library; this is a placement envelope, not a placed memory compiler floorplan.
- Latency sensitivity scales the score32 baseline by HBM byte-share change only; HBM/DRAM service remains inherited.

## Next Step

- Prioritize HBM/DRAM service closure if the conservative SRAM placement envelope does not materially change hbm_byte_share; otherwise revisit SRAM hierarchy capacity.
