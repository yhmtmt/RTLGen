# Analysis Report

The 8-packet contention case matches exactly at 88 cycles, 171 contention
cycles, 53 input stalls, and peak router occupancy 29.

The complete local Llama7B replay, including one-cycle command prefetch, also
matches exactly:

- packets/flits: 11,576 / 92,128
- serial scheduler drain: 397,227 cycles
- merged endpoint-parallel baseline: 397,203 cycles
- serialization cost: 24 cycles (0.006%)
- contention: 8,736 versus 30,285 baseline
- input stalls: 11,816 versus 46,504 baseline
- peak occupancy: 7 versus 11 baseline
- prefetch requests/responses/deliveries: 11,576 / 11,576 / 11,576

Remote reproduction remains the promotion evidence.
