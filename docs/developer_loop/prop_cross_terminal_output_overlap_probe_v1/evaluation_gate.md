# Evaluation Gate

- status: approved_for_local_audit_only
- approved_by: user
- approved_utc: 2026-03-18T07:16:43Z
- allowed_evaluations:
  - local overlap audit on the accepted `nm1` non-fused baseline trace and the
    fused-output schedule evidence
  - local benchmark-selection check for one terminal-output-sensitive proof
    setup on a fixed architecture
  - no remote L2 campaign yet
- note:
  The baseline perf trace already suggests hidden terminal-copy cost:
  `SOFTMAX` runs from `493 ns` to `621 ns`, while `dma_y` runs from `500 ns` to
  `564 ns`. The next step is to determine whether that overlap is intentional
  and semantically valid. Only after that audit should this proposal request a
  remote `{non-fused, fused}` rerun under either a validated no-overlap proof
  setup or a more terminal-output-sensitive benchmark slice.
