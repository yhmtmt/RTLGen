# Numerical replay implementation validation

The opt-in `test_numerical_mesh_rtl.py` diagnostic passed locally in 429.11 s.
It exercises numerical leaf/root file loading, command base 0x8200, sixteen
distinct release schedules, all 512 finalized rows, 8192 source handshakes,
and recorded arbitration/model agreement through the full shared-mesh RTL.

Inputs are synthetic: each leaf has maximum zero, exponential sum one, and
eight unit numerators. The expected finalized values are Q16 unity (65535).
This proves the numerical replay mechanism for that fixture, not numerical
equivalence of the measured cluster outputs. The all-cluster collector remains
the required source for the next measured-data replay.

Reproduction:

```sh
RTLGEN_RUN_NUMERICAL_MESH_DIAGNOSTIC=1 python -m pytest -q npu/eval/tests/test_numerical_mesh_rtl.py
```

The numerical driver is `npu/eval/run_numerical_mesh.py`. It accepts the
all-sixteen-cluster collection, checks payload metadata and widths, and uses
each endpoint's own measured cycles. Canonical addressed K/V ingress, direct
producer-to-mesh backpressure composition, routed PPA, CDC, and activity power
remain outside this diagnostic.
