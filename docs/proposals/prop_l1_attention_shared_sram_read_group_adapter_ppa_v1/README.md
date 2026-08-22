# Shared-SRAM read-group adapter PPA

This package measures the logic that converts ordered 256-bit NoC reads or
512-bit local-fill reads into 1024-bit shared-SRAM macro accesses.  The four
points cross output width (256/512) with one/two collection slots.

RTL equivalence proves exact ordered payload and address replay, stable
backpressure, fail-closed malformed metadata handling, and access ratios of
four 256-bit or two 512-bit beats per macro read.  Two slots sustain one
output beat per cycle after fill with a macro response latency up to two
cycles.

These runs measure adapter and narrow-I/O activity-harness standard cells
only.  They must not include a fabricated 68 MiB RTL array.  Full shared-SRAM
capacity area and per-access energy come from the checked CACTI macro registry
and are composed separately by
`npu/eval/audit_llama7b_shared_sram_access_energy.py`.

The physical harness keeps the complete response bus and all payload state but
folds only the endpoint lanes into its narrow checksum.  Its metadata-derived
macro response repeats one 32-bit lane, avoiding a wide arithmetic stimulus
generator.  Payload registers are intentionally unreset because slot-valid
state guards every architectural read.

Bounded Nangate45 generic mapping retains 1,024 payload DFFs for one-slot
points and 2,048 for two-slot points, with zero structural problems:

| Point | Adapter um2 | Generated top um2 | Core utilization |
|---|---:|---:|---:|
| w256/s1 | 14,642.502 | 16,736.454 | 24.76% |
| w256/s2 | 23,825.354 | 25,919.306 | 38.34% |
| w512/s1 | 14,154.392 | 16,248.078 | 24.04% |
| w512/s2 | 23,743.958 | 25,837.644 | 38.22% |

These are pre-route estimates only.  The corrected OpenROAD sweep uses a
260-by-260 um core at placement density 0.50; the former 200-by-200 um core at
0.45 density could not place either two-slot point.

The adapter is one macro-port building block, not a complete K producer.  The
exact tensor-layout model shows that each home needs 17 interleaved macro
banks and a double-buffered 16 KiB K word window to sustain the 128-dimension
producer cadence.  That bank scheduler remains the next physical gate.
