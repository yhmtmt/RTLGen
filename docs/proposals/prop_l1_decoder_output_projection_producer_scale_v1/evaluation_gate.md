# Evaluation Gate

Accept the job if it:

- runs all three producer configs at `num_modules=4`, `8`, and `16`
- keeps `SYNTH_HIERARCHICAL=1` and preserves `gemm_compute_array`
- reports per-config `metrics.csv` with timing, area, and power
- clearly separates producer-side block PPA from final combined producer/ranker
  macro PPA
