Evaluation Agent Guidance
=========================

Purpose
-------
This document defines how evaluator agents should:
- Discover new evaluation targets (beyond existing campaigns).
- Interpret unexpected PPA results.
- Decide between OpenROAD flow retuning vs design warnings.
- Record findings for RTLGen algorithm developers and coding agents.

Target Discovery (Beyond Campaigns)
----------------------------------
Agents should not only run queued configs in `runs/campaigns/`. They should
proactively explore RTLGen configuration space when gaps are found.

Priority heuristics:
- Missing cross-product: widths/PPG/CPA/signedness combinations not yet in
  `runs/designs/` or `runs/index.csv`.
- Platform coverage gaps: identical configs not evaluated across all PDKs.
- Unbalanced exploration: too few data points for a specific CPA family or
  Yosys booth mode.
- Edge cases: minimum widths (4/8), signed vs unsigned, and Yosys LowpowerBooth
  (signed-only) to reveal architectural penalties.

Recommended discovery loop:
1) Parse `runs/index.csv` to enumerate evaluated (circuit_type, design, pdk).
2) Generate candidate configs from RTLGen’s configuration space (see
   `examples/about_config.md`).
3) Skip those already evaluated, then queue or run the missing ones.

Reasoning About Unexpected Results
---------------------------------
When PPA behavior looks inconsistent, classify the cause:

1) Flow optimality issue (retune OpenROAD)
- Symptoms:
  - Timing is much worse at low utilization but improves sharply at higher util.
  - Area/power swings are unusually large for similar designs.
  - Route/PDN failures or congested placements for tiny blocks.
- Action:
  - Run a parameter sweep (core utilization, place density, clock period).
  - Keep best results and log the tuned parameters.

2) Design-level issue (flag RTL/arch)
- Symptoms:
  - Degradation across all flow settings and PDKs.
  - Persistent area inflation or delay regression vs comparable designs.
  - Lowpower Booth or signedness options hurting results beyond expected trend.
- Action:
  - Log as a design warning and include evidence.
  - Reference likely root causes (extra recoder logic, wider PP array, etc.).

3) Data/metric issue (fix evaluation data)
- Symptoms:
  - Outliers tied to a single run ID or malformed metrics.
  - Incomplete metrics (missing power or delay) without failures.
- Action:
  - Rerun or clean the row; update `runs/index.csv`.

Logging Requirements
--------------------
Evaluator outputs should be summarized in a short note (Markdown) placed under:
- `notes/evaluation_notes/<topic>.md`

Each note should include:
- Scope: what was evaluated (designs, widths, PDKs).
- Observation: what looks unexpected or suboptimal.
- Classification: flow optimality vs design issue vs data issue.
- Evidence: relevant metrics or plots (with path references).
- Next step: suggested action (retune params / RTL change / new configs).

Evaluation Directory Hygiene
----------------------------
When running new evaluations (even if the circuit type matches previously
evaluated ones), always create a new, distinctive design directory and
campaign name:
- `runs/designs/<circuit_type>/<new_design_name>/...`
- `runs/campaigns/<circuit_type>/<new_campaign_name>/...`

This keeps results traceable to the algorithm or parameter changes under
evaluation and avoids mixing metrics with historical baselines.

OpenROAD Retuning Guidance
--------------------------
When the issue is likely flow-related:
- Sweep `CORE_UTILIZATION`, `PLACE_DENSITY`, and `CLOCK_PERIOD`.
- For tiny designs, low utilization often reduces PDN/route failures.
- Compare results against the current best in `runs/campaigns/*/best_*.csv`.

Design Warning Guidance
-----------------------
When the issue is likely architectural:
- Compare against a baseline with identical width/signedness and a known CPA.
- Note if the regression is PDK-specific (e.g., ASAP7 area spike).
- Log a concise hypothesis for algorithm developers.
