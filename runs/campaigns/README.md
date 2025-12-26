Runs Campaigns
==============

This directory stores evaluation campaigns: input configs, sweep definitions,
and summary tables for a group of designs.

Layout
------
- `runs/campaigns/<circuit_type>/<campaign>/configs/`
- `runs/campaigns/<circuit_type>/<campaign>/sweeps/`
- `runs/campaigns/<circuit_type>/<campaign>/*_summary.csv`
- `runs/campaigns/<circuit_type>/<campaign>/best_*.csv`

Notes
-----
- Campaign scripts should write design outputs into `runs/designs/`.
- Summaries typically reference `runs/designs/.../work/*/result.json`.
