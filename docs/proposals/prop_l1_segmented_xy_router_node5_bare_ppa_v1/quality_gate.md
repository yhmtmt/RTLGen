# Quality Gate

- Staged FIFO, router, and specialization sources are byte-identical to the
  canonical RTL replay sources.
- The specialization contains no sequential or combinational behavior and
  instantiates exactly one router.
- Yosys `hierarchy -check`, `proc`, and `check` pass for the physical top.
- Cycle-by-cycle `in_ready`, every forwarded flit field and payload, and final
  router counters remain exactly equivalent to the performance replay.
