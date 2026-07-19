# Shared-score multivalue cluster activity power

- decision: `activity_power_rejected_no_gated_candidate`
- promoted candidates: `0`
- measured candidates: `1`

| variant | path ns | instance mm2 | status | head cycles | head latency ms | energy mJ |
|---|---:|---:|---|---:|---:|---:|
| decode_score_multivalue_cluster_v1_8ns_bridge_proxy_die_2500 | 7.1765 | 2.785000 | measurement_failed | None | None | None |

## Remaining Abstractions

- FakeRAM area and power use Nangate45 proxy LEF/Liberty views, not SRAM compiler signoff.
- Value-memory, NoC, HBM/DRAM, command-distribution, and clock-tree composition outside the cluster are not included.
- RTL VCD is mapped to the routed netlist; each candidate records and gates direct annotation coverage.
- Score multiplier and shift derivation remain external to the cluster boundary.
