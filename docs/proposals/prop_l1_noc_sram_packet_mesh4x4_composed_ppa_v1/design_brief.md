# Design Brief

## Included Structure

- Sixteen descriptor-driven SRAM packet endpoints.
- Sixteen five-port, four-VC, depth-four deterministic-XY routers.
- All 24 bidirectional 256-bit neighbor links.
- Registered-occupancy FIFO credits with no network-wide ready fixpoint.
- Collision-free descriptor installation and packet release control.
- One bounded in-order source-SRAM response slot per endpoint.
- Destination-SRAM write and completion backpressure.
- Packet lengths 1..8, all VCs, all sources, and an odd-stride destination
  permutation.

## Compact Observability

Each destination captures a local 16-bit payload slice. The selected slice
rotates by epoch, so every one of the 256 transported payload bits remains
structurally observable without a global 4096-bit port or XOR timing path.
Packet counters, endpoint-valid bits, and aggregate protocol error are exposed.

## Comparison

Use the same 3.2 mm square die/core envelope, 45 percent placement density,
and 2.0 ns target as the aggregate-mesh feasibility point. Report absolute PPA
and the disclosed delta from aggregate mesh plus separately measured endpoint
anchors. Do not interpret vectorless power as Llama7B traffic energy.
