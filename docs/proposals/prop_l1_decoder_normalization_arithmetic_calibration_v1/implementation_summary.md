# Implementation Summary

Pending evaluator work.

The developer-side change for this proposal is documentation and control-plane
setup:

- the decoder cost-estimator reports now mark cost units as uncalibrated
  heuristic planning units;
- this proposal records the L1 measurements needed to start calibrating those
  terms with RTLGen/OpenROAD evidence.
