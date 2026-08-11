# Score32 NoC Phase 2 Schedule

This proposal introduces a Phase 2 score32 NoC schedule report that:

- consumes the existing Llama7B score32 recost artifact and measured L1 cost profile
- materializes an explicit static 4x4 mesh mapping for shared-SRAM and root-reduction traffic
- uses the cycle-by-cycle multi-flow segmented mesh model instead of a one-flow bandwidth scalar
- converts compute-wrapper release cycles into absolute NoC cycles using explicit
  clock periods before routing

The checked-in report generator now defaults to the full declared workload. A lightweight bounded run is still available, but only when `--wave-limit` is passed explicitly. The requested L2 job stays intentionally lightweight, with no HBM/DRAM timing claim and no DB insertion from this patch.

The original unrun v1 queue item is superseded: it treated compute cycles as
NoC cycles. The immutable `_r1` retry uses a 1ns target NoC clock and retains
measured-router-clock substitution as a required follow-on.
