Purpose
-------
- Track evaluated RTLGen configurations in a lightweight, repo-visible way (configs, generated Verilog, and CSV metrics only).
- Provide a queue for unevaluated configs: add a JSON config here to invite others to run it and append metrics.

Layout
------
- `runs/<circuit_type>/<design>/config.json` — the config that produced the metrics (e.g., `runs/prefix_adders/adder_ripple_4u_wrapper/config.json`).
- `runs/<circuit_type>/<design>/verilog/*.v` — generated RTL for that config (no DEF/GDS/logs).
- `runs/<circuit_type>/<design>/metrics.csv` — aggregated execution parameters and parsed metrics per run; new sweeps append rows.
- `runs/<circuit_type>/<design>/work/` — transient per-run scratch (may be cleared without losing the published artifacts).

Evaluated
---------
Prefix adders (unsigned):
- Families: Ripple, BrentKung, KoggeStone, Sklansky across widths 4/8/16/32/64.
- PDKs: Nangate45, Sky130HD, ASAP7.
- Summaries: `runs/prefix_adders/nangate45_unsigned_summary.csv`, `runs/prefix_adders/sky130hd_unsigned_summary.csv`, `runs/prefix_adders/asap7_unsigned_summary.csv`.
- Sweep settings: small blocks use `CORE_UTILIZATION=10` (and relaxed variants for stubborn cases) to avoid PDN/route failures.

Multipliers:
- Width sweep (Nangate45/Sky130HD/ASAP7): 4/8/16/32-bit, signed+unsigned, PPG {Normal, Booth4}, CPA {Ripple, KoggeStone, BrentKung, Sklansky}.
  - Summaries: `runs/multipliers/ppg_cpa_widths_4_32/nangate45_summary.csv`, `runs/multipliers/ppg_cpa_widths_4_32/sky130hd_summary.csv`, `runs/multipliers/ppg_cpa_widths_4_32/asap7_summary.csv` (64 rows each); replaces earlier 16-bit-only pilot sweeps.

Observed Trends (config choice -> results)
------------------------------------------
Prefix adders:
- CPA choice dominates timing/area: KoggeStone and Sklansky are consistently fastest but largest area/power; Ripple is smallest area/power but slowest; BrentKung is in-between.
- Scaling with width: Ripple degrades steeply with width; prefix adders stay relatively flat, especially KoggeStone/Sklansky.

Multipliers:
- CPA choice dominates timing and area: KoggeStone/Sklansky give the best delay, Ripple is slowest, BrentKung is intermediate.
- PPG choice (Normal vs Booth4) shows weak platform dependence: Booth4 is slightly smaller and a hair faster on Nangate45; slightly smaller but slower on Sky130HD; slightly larger and slower on ASAP7. The ordering is consistent across CPAs, signedness, and widths 4–32.
- Signed vs unsigned: signed variants generally trend slightly larger area/power at the same CPA/PPG, with similar timing.
- High-utilization sweeps (dense floorplans) across Nangate45/Sky130HD/ASAP7: see `best_area_highutil.csv` for highest-util area picks per platform; a single relaxed Nangate45 point (mult4u_normal_ripple) is included because the 50–60% targets failed. Dense runs shrink area notably (especially on ASAP7) with small delay impact. For delay/power outliers, see `best_delay_highutil.csv` (dense-only) and `best_delay_all.csv`/`best_power_all.csv` (best across all util points) to spot cases where lower-util runs win timing/power.

Contribute
----------
- Add a new config under `runs/<circuit>/config.json` (or a variant name) and open a PR; keep configs minimal and documented.
- Run `scripts/run_sweep.py ... --out_root runs` locally; it will append rows to `metrics.csv` and refresh `verilog/`.
- If you can’t run flows, still contribute literature context: add brief design notes and paper links in `plan/log.md` or include a `README.md` beside the config summarizing the idea, target metrics, and references.
- Do not check in large binaries (logs/DEF/GDS); keep this directory light to encourage frequent evaluation by others/agents.
