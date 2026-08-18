# Design Brief

The replay fetches globally ordered 102-bit command records through a concrete
one-cycle SRAM request/response controller with one outstanding read and one
response buffer. The paired scheduler alone drives endpoint RX/TX descriptors.
All packet payload, SRAM-port, endpoint, router, and completion behavior remains
identical to the merged finite endpoint baseline.
