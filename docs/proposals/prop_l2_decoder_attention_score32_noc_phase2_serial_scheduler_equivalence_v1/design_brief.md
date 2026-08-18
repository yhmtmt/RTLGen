# Design Brief

The replay streams globally ordered 102-bit command records from an external
memory model into the concrete scheduler. The scheduler alone drives endpoint
RX/TX descriptors. All packet payload, SRAM-port, endpoint, router, and
completion behavior remains identical to the merged finite endpoint baseline.
