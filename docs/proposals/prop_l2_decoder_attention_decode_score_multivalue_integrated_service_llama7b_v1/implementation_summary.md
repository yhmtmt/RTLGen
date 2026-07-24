# Implementation Summary

## Scope
- Added the `decoder_attention_decode_score_multivalue_integrated_service`
  L2 abstraction hook to the control-plane task generator.
- Wired compact JSON/Markdown evidence outputs and result-consumer recognition.
- Expanded the probe to the requested bounded 14-case matrix through
  `cluster_count=32`.
- Recorded `l2_decoder_attention_decode_score_multivalue_integrated_service_llama7b_v1`
  as superseded before merge: PR #1436 passed its functional gates, but its
  committed JSON repeated generated-manifest and preload payloads. The clean
  rerun target is `..._v1_r1`.

## Evidence Contract
- JSON now retains:
  - exact Python/baseline/integrated hashes
  - protocol/count gate booleans
  - completion and service penalty cycles
  - shared-result blocking/arbitration counters
  - router/service contention and occupancy maxima
  - explicit exclusions
  - proposal/dependency linkage
- JSON now deduplicates shared preload/manifest/top identities at the report
  level and enforces a pretty-printed compactness gate of `<=100000` bytes /
  `<=2500` lines.
- Markdown now summarizes the same evidence in a compact per-case table.
- The largest nominal round-robin coverage point is labeled
  `selected_scale_point`; it is explicitly not an architectural or performance
  ranking and is not consumed as a decoder recommendation.

## Local Validation
- focused pytest coverage for:
  - probe defaults and linkage
  - compact report shape rejection
  - full-matrix size regression with oversized synthetic manifests
- passed `pytest -q tests/test_attention_decode_score_multivalue_integrated_service.py`
- passed `python3 -m py_compile npu/eval/probe_attention_decode_score_multivalue_integrated_service.py`
- passed real 14-case `build_report()` probe on Friday, July 24, 2026 UTC with compact output size `67278` bytes / `1690` lines (`403110` bytes / `11271` lines in the superseded PR #1436 artifact)
