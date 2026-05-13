# Implementation Summary

Adds diagnostic `cq_mem_ablation_mode` support to `npu/rtlgen/gen.py`, defaulting to the existing full command-queue decode path.

Adds `npu/eval/probe_decoder_producer_cq_ablation.py` and wires it into the L2 task generator as `decoder_output_projection_producer_cq_ablation`.

The probe writes temporary variant configs under `runs/designs/npu_blocks`, generates RTL, captures static Verilog size counters, and runs bounded synth-only OpenROAD flow per CQ subpath variant.
