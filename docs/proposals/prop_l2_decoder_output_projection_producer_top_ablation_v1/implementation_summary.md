# Implementation Summary

Adds `npu/eval/probe_decoder_producer_top_ablation.py` and wires it into the L2 task generator as `decoder_output_projection_producer_top_ablation`.

The script writes temporary variant configs under `runs/designs/npu_blocks`, generates RTL, captures static Verilog size counters, and runs bounded synth-only OpenROAD flow per variant.

