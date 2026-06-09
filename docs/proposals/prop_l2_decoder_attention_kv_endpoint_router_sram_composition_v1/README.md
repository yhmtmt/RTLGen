# Endpoint Router/SRAM Composition Audit

This proposal audits the current Llama7B on-chip frontier against concrete
endpoint ready/valid evidence, measured NoC router/FIFO PPA, and measured
tile-local SRAM metrics.

The purpose is to prevent narrow primitive PPA from being treated as a closed
wide-link implementation. HBM/DRAM service remains intentionally out of scope.
