# Design Brief

## Included

- Sixteen canonical five-port, 256-bit deterministic-XY routers.
- Four virtual channels, depth-four input FIFOs, and all inter-router links.
- All sixteen functional endpoint ready/valid, payload, and metadata ports.
- Mesh clock tree and aggregate routed-wire effects.

## Excluded

- Synthetic traffic generation and compact observation registers.
- Debug counter output pins; counters are verification instrumentation rather
  than part of the deployed transport interface.
- Packet endpoints, SRAM macros, producers/reducers, and HBM/DRAM.

The functional boundary has 8,962 scalar pins. At the measured 1.12 um/pin
placement bound it requires 10,037.44 um of perimeter, below the 12,800 um
available on the 3.2 mm square feasibility envelope.
