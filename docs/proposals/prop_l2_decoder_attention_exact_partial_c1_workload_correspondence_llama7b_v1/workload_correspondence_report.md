# Exact-partial c1 workload correspondence

## Result

The bounded finalized-CDC RTL matrix passes for divider lanes 1, 2, 4, and 8
at the selected 10 ns service / 12 ns temporal clocks. Each lane has the same
macro-backed reset-to-last-service-terminal measurements:

| Full windows | Service cycles |
|---:|---:|
| 1 | 1,051 |
| 2 | 2,127 |
| 3 | 3,203 |
| 4 | 4,279 |

All three counter deltas are exactly 1,076 cycles. The only projected service
counter therefore uses the proven affine recurrence:

`S(N) = 1,051 + (N - 1) * 1,076`

For 5,462 windows/head, `S = 5,877,087` service cycles/head. The recurrence
conservatively charges the final 8-token partial as a full window. The bounded
three-full-plus-tail RTL case passes with 160 distinct refill writes and is 670
service cycles shorter than four full windows, but that saving is not used in
the projection.

## Serial Bounds

| Divider lanes | Final drain temporal cycles/head | Service cycles/layer | Serial latency bound/layer (ns) |
|---:|---:|---:|---:|
| 1 | 7,328 | 188,066,784 | 1,883,481,792 |
| 2 | 3,680 | 188,066,784 | 1,882,080,960 |
| 4 | 1,856 | 188,066,784 | 1,881,380,544 |
| 8 | 944 | 188,066,784 | 1,881,030,336 |

The 32-layer serial service bound is 6,018,137,088 cycles. Final-drain bounds
for 32 layers are 7,503,872, 3,768,320, 1,900,544, and 966,656 temporal cycles
for divider lanes 1, 2, 4, and 8 respectively.

## Correspondence Checks

- Window counts 1, 2, 3, and 4 match exact software values and every modeled
  refill, request, response, merge, state-memory, emission, and finalizer count.
- Every window has distinct values and performs a real macro-store refill before
  its command. Output equality therefore detects stale or omitted refill traffic.
- The 8-token tail uses one active block after three full three-block windows.
- A two-head case reuses the same temporal head slot without reset. Both heads
  match independent references, proving state clear/reuse.
- Each logical head emits and finalizes exactly 16 slices once, only after its
  final window. Protocol errors fail the probe.

## Assumptions

- One c1 instance schedules windows and heads serially; no head/layer overlap is
  credited in the bounds.
- A full window is three 8-token blocks; 131,072 tokens are 5,461 full windows
  plus one 8-token tail.
- The final drain is 16 slices times the RTL finalizer accept interval:
  `57 * (8 / divider_lanes) + 2` temporal cycles.
- Elapsed testbench `service_cycles`, `temporal_cycles`, and `finalizer_cycles`
  include CDC phase and overlap. They are diagnostic and are not extrapolated.
  The affine guard applies to the explicitly defined reset-to-terminal service
  span used by the projection.

Machine-readable bounded evidence and assumptions are in
`workload_correspondence_report.json`.
