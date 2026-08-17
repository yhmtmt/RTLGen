# Llama7B Phase-2 Endpoint/RTL Equivalence

- coverage: `workload_complete`
- packets/flits: `11576` / `92128`
- logical release-queue drain: `397004` cycles
- finite endpoint/RTL drain: `397203` cycles
- endpoint cadence delta: `199` cycles
- router contention/input stalls: `30285` / `46504`
- maximum router occupancy: `11`
- maximum RX contexts used per endpoint: `8`
- cycle and router counter equivalence: `true`

## Remaining Abstractions

- SRAM arrays are transaction-accurate one-cycle ports; bitcells and macro placement remain external.
- The command scheduler is embodied by the deterministic paired-descriptor testbench driver, not yet synthesized RTL.
- HBM/DRAM and its controller remain intentionally outside the design boundary.
- Workload-matched switching power requires a separate activity-capture run.
