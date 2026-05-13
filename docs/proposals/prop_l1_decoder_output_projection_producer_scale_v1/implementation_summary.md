# Implementation Summary

- Add three fp16 NPU producer block configs with `compute.gemm.num_modules`
  set to 4, 8, and 16.
- Add a hierarchy-preserving Nangate45 sweep that keeps `gemm_compute_array`
  as the measured producer boundary.
- Queue one Layer 1 sweep item to collect timing, area, and power for the
  producer scaling curve.
