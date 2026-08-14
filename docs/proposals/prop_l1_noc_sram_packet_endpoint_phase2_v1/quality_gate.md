# Quality Gate

- TX payload data advances only through accepted SRAM responses and router
  handshakes.
- TX flits remain stable under router backpressure.
- RTL TX metadata exactly matches `packetize_traffic_flow` for one- through
  eight-fragment packets.
- RX accepts interleaved packet contexts and writes exact fragment addresses.
- Completion backpressure cannot release a receive context early.
- Valid bounded traffic finishes with `protocol_error=0`.
- Generated compact harness compiles, runs, and retains live issued/completed
  packet progress.
- Yosys hierarchy/procedure/check passes without conflicting-driver errors.
