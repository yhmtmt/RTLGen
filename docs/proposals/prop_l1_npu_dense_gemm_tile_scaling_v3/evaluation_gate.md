# Evaluation Gate

- status: approved_after_source_merge
- approved_by: developer_agent
- approved_utc: 2026-06-22T00:00:00Z
- allowed_evaluations:
  - Run `l1_npu_dense_gemm_tile_scaling_v3` as a hierarchy-preserving Layer 1
    PPA sweep on the remote evaluator only.
- required_machine: `eval-daemon-b7c2d9c80c1c`
- note: The queued payload must include `source_requirement.required_sha` for
  the merged commit containing this proposal, the V3 sweep, and the new dense
  tile configs.
