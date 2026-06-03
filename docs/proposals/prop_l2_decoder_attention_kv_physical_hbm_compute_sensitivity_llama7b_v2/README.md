# Llama7B Physical HBM Compute Sensitivity

This proposal measures the compute-throughput boundary for Llama7B 131k
single-token decode attention after the local L1 datapath costs were replaced
with measured RTL/PPA values.

The question is whether the practical high-SRAM, physical-HBM region is still
limited by memory/interconnect service, or whether the current measured compute
throughput is too small to represent the larger Llama7B frontier. The requested
job sweeps MAC/cycle and vector-op/cycle against fixed native-GQA KV8,
HBM-stack, SRAM-capacity, and simple NoC assumptions.

This is an architecture planning pass. It does not introduce new RTL, does not
change token quality assumptions, and does not claim a routed global NoC.
