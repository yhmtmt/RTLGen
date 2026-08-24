# Design Brief

Each transaction group collects one 1024-bit shared-SRAM word as four 256-bit
or two 512-bit beats, issues one macro read, and emits the original beats in
order. A second slot overlaps collection with macro service and emission.

The evaluator replays the generated RTL for 64 groups with deterministic
response backpressure. It compares every externally reported count plus the
internal stall counters against a pure cycle model, then attaches the four
merged timing-feasible Nangate45 rows at a common 2 ns target.
