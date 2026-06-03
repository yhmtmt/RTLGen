# Llama7B Attention/KV Compute Floor Gap

This proposal quantifies the gap between the merged Llama7B 131k HBM-bound
compute floor and the compute throughput achievable from the currently measured
NPU compute blocks.

The purpose is to decide whether the next frontier work should deepen SRAM/NoC
simulation or first pursue a denser compute architecture. The result shows that
the current measured compute density is far below the first HBM-bound floor, so
compute architecture remains the immediate blocker.
