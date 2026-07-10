# Score32 Separated Compute Recost

This proposal dispatches a measured-component recost of the current quality-aware score32 Llama7B frontier.

The audit keeps the mixed-int8 schedule latency and external traffic terms, then replaces the fully replicated score32 wrapper subtotal with separated dense-int8 GEMM, shared vector-softmax overhead, command dispatch, and measured HBM replay-controller PPA components. It records that the inherited energy row is q8/k8/v6 reciprocal-LUT while the quality target is q8/k8/v8 score32 exp-LUT/div, so it does not attribute the target quality across that profile mismatch. The output is evidence for prioritizing precision-aligned composed RTL work, not a promotable full-path closure.
