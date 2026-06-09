# Endpoint Ready-Valid Service Probe

This proposal validates the selected endpoint full on-chip service point against
the concrete `onchip_service_endpoint.sv` ready/valid RTL block.

The job consumes the finalized endpoint full on-chip service schedule, derives
the packet width and finite queue depths from the best row, runs an endpoint
backpressure probe, and reports the RTL parameters and counters.

HBM/DRAM service, router routing, and SRAM macro timing are intentionally out of
scope for this item.
