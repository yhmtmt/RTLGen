# Evaluation Gate

- status: pending_contract_confirmation
- approved_by: user
- approved_utc: 2026-03-18T07:16:43Z
- allowed_evaluations:
  - local overlap-audit implementation and targeted simulator regression
  - local benchmark-selection check for one terminal-output-sensitive proof
    setup on a fixed architecture, if the event contract remains unchanged
  - no remote L2 campaign yet
- note:
  The local audit produced a concrete explanation for the flat fused result.
  Under the old overlap model, the accepted baseline trace let terminal
  `dma_y` run from `500 ns` to `564 ns` while `SOFTMAX` was still active from
  `493 ns` to `621 ns`. After enforcing completion-bound event signaling in the
  local perf model, the same descriptor stream moves terminal `dma_y` to
  `853.75 ns -> 917.75 ns` and total simulated time rises to `967.75 ns`.
  Remote spend stays blocked until we confirm whether that contract is the
  intended shell behavior.
