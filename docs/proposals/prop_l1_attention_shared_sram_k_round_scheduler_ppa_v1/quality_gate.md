# Quality Gate

- Match all 1,024 block-major stride-8 addresses, bank assignments, response
  identities, and compute beats between RTL and the executable model.
- Preserve the final round's nine-word valid mask and all output ordering.
- Hold requests and compute output stable under independent backpressure.
- Reject stale, duplicate, wrong-bank, and out-of-round responses fail closed.
- Retain exactly 34,816 live payload bits through physical-harness synthesis.
- Treat the checksum and replicated synthetic response source as activity/PPA
  support only, never as equivalence evidence.
