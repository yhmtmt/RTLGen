# Quality Gate

- Preserve every input payload bit and emit beats in accepted order.
- Issue exactly one 1024-bit macro transaction per four 256-bit beats or two
  512-bit beats.
- Hold all ready/valid payload and metadata stable under backpressure.
- Reject malformed or stale response metadata without emitting data.
- Do not instantiate or claim PPA for the full shared-SRAM capacity.
- Treat activity checksums as PPA retention diagnostics, not equivalence proof.
