Booth4 vs Normal PPG (4/8/16/32-bit multipliers)
=================================================
- Inputs: `runs/multipliers/ppg_cpa_widths_4_32/{nangate45,sky130hd,asap7}_summary.csv`
- Method: aggregate Booth4–Normal deltas per width by averaging across signed/unsigned and all CPAs (Ripple/BrentKung/KoggeStone/Sklansky).
- Outputs:
  - `delta_by_width.csv` — per-platform per-width mean deltas for `critical_path_ns`, `die_area`, and `total_power_mw` (Booth4 minus Normal).
  - `delta_metrics_by_width.png` — plot of the same deltas (critical-path/area/power) vs width for each platform.
