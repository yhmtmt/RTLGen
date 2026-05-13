# Implementation Summary

Extends diagnostic `cq_mem_ablation_mode` support in `npu/rtlgen/gen.py` with finer SOFTMAX/EVENT descriptor branch modes.

Adds `npu/eval/probe_decoder_producer_softmax_event_ablation.py` and wires it into the L2 task generator as `decoder_output_projection_producer_softmax_event_ablation`.

The probe writes temporary variant configs under `runs/designs/npu_blocks`, generates RTL, captures static Verilog size counters, and runs bounded synth-only OpenROAD flow per SOFTMAX/EVENT subpath variant.
