# Design Brief

## Structure

- Four-entry TX descriptor FIFO.
- Eight-entry in-order SRAM-request metadata queue.
- Stable 256-bit ready/valid router injection interface.
- Eight receive contexts keyed by `(source, VC, tag)`.
- Direct fragment writes to destination SRAM and buffered packet completion.
- Sticky protocol checking for invalid descriptors, duplicate live keys,
  missing contexts, wrong destination, fragment order, and `last` consistency.

## Physical Harness

- Internally install matching TX and RX descriptors with packet lengths 1..8.
- Cycle all four VCs, tags, destinations, source/destination addresses, and all
  256 payload bits.
- Apply SRAM-read, SRAM-write, and completion backpressure.
- Observe TX metadata, payloads, RX addresses/data, completion metadata,
  issued/completed counts, and protocol status through a compact boundary.
- Retain the local-destination comparator through a four-bit destination probe
  instead of tying it to a synthesis-removable constant. Register that probe at
  the physical wrapper so every measured data path has a macro timing boundary.

## Exclusions

- SRAM macros and bitcells.
- Router and aggregate mesh wiring.
- Producer/reducer arithmetic and root finalization.
- HBM/DRAM and workload-derived switching activity.
