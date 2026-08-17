# Evaluation Gate

- The exact hardware row declares hidden size 4096, 32 attention heads, 32 KV heads, and MHA.
- The quality artifact declares the official Llama-2-7B checkpoint with the same dimensions.
- The arithmetic profile is score32 q8/k8/v8, weight16, exp-LUT/div.
- A quality hold leaves the exact row nonpromotable but does not erase its engineering measurements.
- Area uses total embodied logic, memory, NoC/endpoint, and measured HBM-controller area.
- Rows without the same total-embodied-area boundary are reported separately and cannot win the comparable Pareto ranking.
- Rows with different sequence lengths are placed in separate workload-specific winner and Pareto sets.
- Native checkpoint quality can promote only the official 4096-context MHA row, never the 131k extrapolation.
- Energy status and remaining abstractions are reported alongside values.
