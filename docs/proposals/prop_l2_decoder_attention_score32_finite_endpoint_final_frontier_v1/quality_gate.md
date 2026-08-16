# Quality Gate

- Require the exact merged finite-endpoint composed recost.
- Require passing quality evidence for score32 and the exact-FP16 reference.
- Exclude quality-invalid and planning-only rows from the promoted frontier.
- Preserve evidence-status labels for area and energy boundaries.
- Report Pareto and per-dimension winners without an arbitrary scalar score.
- Keep workload activity, SRAM energy, vendor HBM signoff, and native-quality breadth explicit.
