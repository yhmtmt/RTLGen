# Quality Gate

- Focused composed stress case must match RTL and performance simulation on
  packets, flits, cycles, contention, stalls, and occupancy.
- Full replay must cover all eight waves, `11,576` packets, and `92,128` flits.
- Every RX descriptor must precede its paired TX descriptor.
- Endpoint and scheduler protocol-error vectors must remain zero.
- Prefetch request, response, delivered, and scheduler-accepted counts must all
  equal the workload packet count.
