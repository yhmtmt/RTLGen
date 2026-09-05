# Evaluation Gate

Status: pending human approval for the r3 synth-only diagnostic.

The original physical canary is superseded: v1 failed before synthesis because
pre-elaboration module names were selected after parameter elaboration, and r2
reached roughly 17 GiB RSS in hierarchy synthesis without producing rankable
PPA. Neither result is physical infeasibility evidence.

The merged r3 source compares flat and hierarchy-preserving Yosys synthesis at
`make_target=1_2_yosys`, keeps all 120 `fakeram45_64x32` instances as
blackboxes, and excludes macro Liberty during synthesis. Current-master local
plumbing verification passed on 2026-09-05:

```sh
PYTHONPATH=/tmp/rtlgen-r3-audit-KY0WDk:/tmp/rtlgen-r3-audit-KY0WDk/control_plane \
  pytest -q \
  control_plane/control_plane/tests/test_l1_exact_transport_physical_plumbing.py \
  control_plane/control_plane/tests/test_l1_shared_stream_service_physical_plumbing.py
```

Result: 15 passed.

Approval authorizes only the bounded r3 synthesis/resource diagnostic. It does
not authorize a full physical rerun or a PPA/frontier claim. Preserve both
successful and failed mode rows; use the result to choose the next physically
tractable decomposition.
