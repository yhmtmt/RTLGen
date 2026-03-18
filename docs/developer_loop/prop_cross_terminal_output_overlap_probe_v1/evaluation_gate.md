# Evaluation Gate

- status: approved_for_focused_rerun
- approved_by: user
- approved_utc: 2026-03-18T07:16:43Z
- allowed_evaluations:
  - local overlap-audit implementation and targeted simulator / RTL regression
  - one focused remote `{non-fused, fused}` rerun on the fixed `nm1` baseline
    using the corrected event contract
  - no broad nm1/nm2 ranking sweep yet
- note:
  The local audit produced a concrete explanation for the flat fused result and
  the contract has now been aligned locally across both perf and shell paths.
  Under the old overlap model, the accepted baseline trace let terminal
  `dma_y` run from `500 ns` to `564 ns` while `SOFTMAX` was still active from
  `493 ns` to `621 ns`. After enforcing completion-bound event signaling in the
  perf model, the same descriptor stream moves terminal `dma_y` to
  `853.75 ns -> 917.75 ns` and total simulated time rises to `967.75 ns`. The
  generated shell stub now follows the same completion-bound event contract, and
  a focused RTL regression for
  `DMA_COPY -> EVENT_SIGNAL -> EVENT_WAIT -> DMA_COPY` passes.
