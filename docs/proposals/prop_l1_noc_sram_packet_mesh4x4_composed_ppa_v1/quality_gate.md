# Quality Gate

- The exact checked-in endpoint/mesh composition is instantiated.
- All sixteen endpoints issue and complete packets under SRAM and completion
  backpressure.
- Every packet key is installed at its destination before source release.
- Packet lengths 1..8 and all four VCs make progress.
- Every endpoint and all 256 payload bit positions remain observable.
- `protocol_error` stays zero during valid generated traffic.
- Verilator reports no `UNOPTFLAT` combinational ready cycle.
- Generated hierarchy compiles from the exact run config.
