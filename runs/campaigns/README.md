Runs Campaigns
==============

This directory stores evaluation campaigns: input configs, sweep definitions,
and summary tables for a group of designs.

Layer interpretation
--------------------
- Layer 1 campaigns: physical synthesis sweeps for module-level candidate
  comparison (timing/area/power/runtime).
- Layer 2 campaigns: NPU model-set evaluations combining mapper, physical data,
  and performance simulation objectives.

Layout
------
- `runs/campaigns/<circuit_type>/<campaign>/configs/`
- `runs/campaigns/<circuit_type>/<campaign>/sweeps/`
- `runs/campaigns/<circuit_type>/<campaign>/*_summary.csv`
- `runs/campaigns/<circuit_type>/<campaign>/best_*.csv`
- For NPU eval campaigns, additional standard files may include:
  - `campaign.json`, `results.csv`, `summary.csv`, `report.md`
  - `pareto.csv`, `best_point.json`
  - `objective_profiles.json`, `objective_sweep.csv`, `objective_sweep.md`

Notes
-----
- Campaign scripts should write design outputs into `runs/designs/`.
- Summaries typically reference `runs/designs/.../work/*/result.json`.
- Keep campaign outputs append-only and traceable to input config hashes and
  selected physical samples.
