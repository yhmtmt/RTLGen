# Promotion Gate

- status: pending
- Require the router, endpoint, and aggregate-mesh dependencies to be merged.
- Require at least one physically completed row before using this as a composed
  timing/area/power anchor.
- Preserve SRAM-macro, workload-activity, and HBM/DRAM exclusions explicitly.
- If physical feasibility fails, retain the result as a bounded architecture
  limit and split the composition only with an explicit hierarchical plan.
