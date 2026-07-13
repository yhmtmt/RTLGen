# Score32 exp-LUT SRAM Hierarchy Envelope

- decision: `score32_exp_lut_sram_hierarchy_envelope_changes_frontier`
- source score32 latency us: `12519.342352`
- source hbm share: `0.983398438`
- nominal efficiency: `0.75`
- nominal shared MiB: `29.015625`
- nominal hbm share: `0.992916107`
- conservative efficiency: `0.55`
- conservative shared MiB: `16.265625`
- conservative hbm share delta: `0.012630462`
- score buffer reserved: `True`
- score buffer macro: `kv_tile_read_buffer`
- score buffer macro count: `32`
- score buffer area mm2: `66.636897`
- score buffer energy mJ/token: `0.277849571328`

## Sweep

| efficiency | KV shared MiB | score area um2 | hbm share | projected latency us | shared envelope um2 | fits |
|---:|---:|---:|---:|---:|---:|---|
| 1.0 | 45.015625 | 66636897.2928 | 0.989009857 | 12590.7796 | 159039885.568626 | True |
| 0.85 | 35.3125 | 66636897.2928 | 0.991378784 | 12620.937679 | 147219550.762334 | True |
| 0.75 | 29.015625 | 66636897.2928 | 0.992916107 | 12640.508864 | 136738345.653741 | True |
| 0.65 | 22.5625 | 66636897.2928 | 0.994491577 | 12660.565687 | 123268055.738622 | True |
| 0.55 | 16.265625 | 66636897.2928 | 0.9960289 | 12680.136872 | 104620686.040775 | True |

## Assumptions

- SRAM macro placement efficiency is modeled as macro_area/envelope_area and swept explicitly.
- Tile-local SRAM area and endpoint/router/FIFO area are reserved before packing shared SRAM.
- Shared SRAM capacity uses the existing CACTI macro library; this is a placement envelope, not a placed memory compiler floorplan.
- When supplied, the measured score-buffer macro set is reserved before packing remaining KV SRAM capacity.
- Latency sensitivity scales the score32 baseline by HBM byte-share change only; HBM/DRAM service remains inherited.

## Next Step

- Prioritize HBM/DRAM service closure if the conservative SRAM placement envelope does not materially change hbm_byte_share; otherwise revisit SRAM hierarchy capacity.
