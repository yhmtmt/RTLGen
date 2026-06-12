# Composed Dual-Stream Attention Datapath

This design measures a bounded local datapath composition for the Llama7B mixed-precision dual-stream attention frontier.

The generated top uses a narrow self-stimulating PPA harness and contains:

- two signed-int8 16x8 dense GEMM streams,
- one shared row-8 int8 softmax-weight generator,
- two q8/v6 full-value stream datapaths,
- per-stream buffer registers and start/done control,
- a result hash that folds every compute, softmax, and value stream output.

This is not a full global scheduler/SRAM/NoC measurement. It is the next physical anchor after the int8-compute substitution model showed `dual_mac` feasibility.
