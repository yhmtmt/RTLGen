# Design Brief

## Goal
Find why whole `npu_top` producer synthesis timed out even though isolated `gemm_compute_array` synthesis is viable through nm4.

## Method
Use the nm2 producer config as a base and synthesize bounded whole-top variants:

- full reference
- no AXI-Lite wrapper files
- no SRAM side models
- no AXI ports
- no command-queue memory/decode ports
- external ports off
- AXI-Lite wrapper top

Each variant records static generated-RTL counters and synth-only status.

