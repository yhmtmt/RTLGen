# NPU Shell Contract (Draft)

This document will define the host-visible control plane and DMA behavior shared
by RTLGen-generated NPUs. It is a placeholder to be expanded once NVDLA is integrated.

Topics to cover:
- Register map and MMIO access rules
- Command queue format and descriptors
- Event/fence model and interrupts
- DMA modes (bulk, strided, gather/scatter)
- Error reporting and debug hooks
