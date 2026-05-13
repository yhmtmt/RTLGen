# Isolated Producer Synthesis Probe

The previous producer synth-boundary run built `rtlgen`, generated nm2 RTL, and then timed out during `npu_top` synth. This probe uses the same generated Verilog but sets the synthesis top to `gemm_compute_array` so the producer arithmetic array is measured separately from the top-level MMIO, queue, DMA, and AXI shell.

It probes nm1 first as the anchor, then nm2. The sweep uses a clockless synth-only target because `gemm_compute_array` is purely combinational.
