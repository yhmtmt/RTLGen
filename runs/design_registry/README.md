# Design Evidence Registry

This directory records reusable design evidence for architecture exploration. It is
intended to keep RTLGen measurements, published accelerator references, and derived
comparison claims separate from transient evaluator jobs.

The registry answers these questions for each architecture decision:

- Which embodied RTLGen design was measured?
- Which source commit, evaluator run, PR, and artifact paths produced the data?
- Which third-party designs are being used as calibration references?
- Are the compared records actually comparable by circuit category, technology node,
  precision, area scope, and workload?
- Has any measurement been invalidated or superseded?

## Files

- `design_registry.schema.json`: JSON Schema for all JSONL record files.
- `internal_designs.jsonl`: RTLGen design points and source artifacts.
- `internal_measurements.jsonl`: Measured RTLGen PPA/performance records.
- `external_designs.jsonl`: Published academic or commercial reference designs.
- `external_measurements.jsonl`: Published or derived metrics for those designs.
- `comparison_claims.jsonl`: Architecture conclusions that cite internal and
  external evidence.
- `validity_notes.jsonl`: Invalidation, supersession, and caveat records.

## Comparability

External measurements are not ranked directly against RTLGen measurements. Every
external measurement carries a comparability class:

- `direct_comparable`: Same circuit function, precision, area scope, and node policy.
- `same_function_different_precision`: Same function but precision differs.
- `same_compute_class_different_workload`: Similar compute block or array, different
  model/dataflow/workload.
- `system_context_only`: Useful system-level reference, not a block-level baseline.
- `trend_reference_only`: Useful only for broad order-of-magnitude sanity checks.
- `not_comparable`: Recorded for provenance but excluded from comparison claims.

Claims should cite at least one internal measurement and classify each external
reference used. If a claim depends only on an analytic projection, its confidence
must be lower than a claim backed by measured RTLGen PPA.

## Node Scaling

Derived node-scaled densities use simple ideal area-density scaling only:

```text
scaled_density = measured_density * (source_node_nm / target_node_nm)^2
```

This is an optimistic calibration aid. It does not account for voltage, timing
closure, SRAM scaling, routing congestion, standard-cell libraries, IO constraints,
or workload utilization.

