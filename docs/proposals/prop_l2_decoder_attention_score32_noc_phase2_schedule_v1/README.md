# Score32 NoC Phase 2 Schedule

This proposal introduces a bounded Phase 2 score32 NoC schedule report that:

- consumes the existing Llama7B score32 recost artifact and measured L1 cost profile
- materializes an explicit static 4x4 mesh mapping for shared-SRAM and root-reduction traffic
- uses the cycle-by-cycle multi-flow segmented mesh model instead of a one-flow bandwidth scalar

The requested L2 job is intentionally lightweight: one simulated wave, no HBM/DRAM timing claim, and no DB insertion from this patch.
