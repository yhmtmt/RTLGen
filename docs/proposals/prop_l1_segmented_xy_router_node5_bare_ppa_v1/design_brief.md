# Design Brief

## Included

- One five-port, 256-bit segmented XY router at mesh coordinate `(1,1)`.
- Four virtual channels and depth-four input FIFOs.
- Exact flit metadata, arbitration, output holding registers, occupancy, and
  diagnostic counters used by the performance model and RTL replay.
- A logic-free specialization top shared by physical implementation and VCD
  generation.

## Excluded

- Synthetic PPA traffic generation and folded observation logic.
- Inter-router links, aggregate mesh placement, and mesh clock tree.
- Packet endpoints, SRAM macros, producer/reducer arithmetic, and HBM/DRAM.

The direct router interface intentionally includes its combinational ready
path. This is a measured interface path, not an accidental unregistered PPA
probe.
