# Quality Gate

- Require all 11,576 commands and 92,128 flits.
- Require exact RTL/performance equality for cycle and router counters.
- Require every RX descriptor before its paired TX descriptor.
- Require zero generator, scheduler, endpoint, and mesh protocol errors.
- Require TX and RX slot lifetimes to be collision-free in both the model and
  RTL, with all addresses confined to the 144,128-byte endpoint extent.

Status: passed locally. All 11,576 commands and 92,128 flits completed in
397,227 cycles with exact performance/RTL counter equality.
