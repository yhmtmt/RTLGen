# Quality Gate

- Require the exact merged finite-endpoint composed recost.
- Distinguish passing arithmetic quality from structural GQA quality.
- Require checkpoint and hardware GQA group sizes to match before promotion.
- Exclude quality-invalid and planning-only rows from the promoted frontier.
- Preserve evidence-status labels for area and energy boundaries.
- Report Pareto and per-dimension winners without an arbitrary scalar score.
- Keep workload activity, SRAM energy, vendor HBM signoff, and native-quality breadth explicit.
- Keep exact Llama-2-7B MHA recost or trained GQA8/QAT evidence as a mandatory follow-on when structures differ.
