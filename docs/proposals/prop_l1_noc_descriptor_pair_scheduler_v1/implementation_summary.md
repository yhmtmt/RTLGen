# Implementation Summary

- Added synthesizable paired descriptor scheduler RTL.
- Added a one-cycle SRAM request/response prefetch controller with one
  outstanding read and one response buffer.
- Added a PPA harness with varying commands, endpoint backpressure, counters,
  and active-lane observation.
- Added direct-generator support, an exact source manifest, config, and sweep.
- Added protocol and generated-hierarchy tests.
- Added a matching serial-plus-prefetch policy to the endpoint/mesh performance model.
