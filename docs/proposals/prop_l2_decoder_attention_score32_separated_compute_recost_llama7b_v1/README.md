# Score32 Separated Compute Recost

This proposal dispatches a measured-component recost of the current quality-aware score32 Llama7B frontier.

The audit keeps the mixed-int8 schedule latency and external traffic terms, then replaces the fully replicated score32 wrapper subtotal with separated dense-int8 GEMM, shared vector-softmax overhead, command dispatch, and measured HBM replay-controller PPA components. The output is still evidence for prioritizing composed RTL work, not a promotable full-path closure.
