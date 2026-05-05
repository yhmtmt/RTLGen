# Decoder Logit-Rank Streaming With Measured Merge PPA

This proposal reruns the L2 decoder logit-rank streaming overlap model after the L1 candidate-stream merge/FIFO block has real Nangate45 PPA.

The job should not change functional semantics. It should confirm that the L2 perf model and L1 RTL share the same ready-valid observable contract: accepted candidate groups, producer stalls, FIFO occupancy, valid masks, final completion, and lower-token-id tie breaking.
